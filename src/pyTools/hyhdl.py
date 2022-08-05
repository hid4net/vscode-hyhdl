# ==============================================================================
# AUTHOR: hid4net<hid4net@outlook.com>
# DESCRIPTION:
# * 使用
# * hyhdl.py/exe [option] <file>
# *   option:
# *     -i: generate instantiation
# *     -t: generate testbench
# *     -p: generate html for preview of vscode
# *     -h: generate html for export
# *   file: Code file path
# * 设计思路
# *     1. 分离 module 声明前后
# *         a. 逐次分离 wave 前后
# *         b. 提取 wave, 转换为 json
# *         c. 从 wave 以外的部分中, 提取表格
# *     2. 提取 module 声明
# *          a. 提取 parameter, ports
# *          b. 提取 parameter, ports 的注释, 作为 description
# *     3. 暂存提取的数据
# *     4. 根据不同的模板, 生成文件
# MODIFICATION HISTORY:---------------------------------------------------------
#    Version | Author | Date       | Changes
#    :-----: | :----: | :--------: | -------------------------------------------
#    0.1     | hid4net | 2022-05-13 | start to coding
#
# ==============================================================================
# %% ---------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote
import yaml
from jinja2 import Environment, FileSystemLoader


# %% ---------------------------------------------------------------------------
# const
# ------------------------------------------------------------------------------
VS_EXT_PATH_PREFIX = "vscode-resource:/"

USAGE_TIPS = """usage: hyhdl {-i|-t|-p|-h} [verilog_code_path] [-T testbench_template_path]
    -i: generate instantiation
    -t: generate testbench
    -p: generate html for preview of vscode
    -h: generate html for export

    verilog_code_path: optional, if None, use %os_temp_dir%/code

    -T testbench_template_path: avaliable only for testbench (-t)

    output: processed_code_path"""
# %% ---------------------------------------------------------------------------
# global variables
# ------------------------------------------------------------------------------
pytools_dir = ""

# %% ---------------------------------------------------------------------------
# local functions
# ------------------------------------------------------------------------------
# -------- 写入到临时文件 --------
def write_to_tmpfile(file_name: str, text: str) -> str:
    """
    将文本写到临时文件\n
    file_name: str => 文件名\n
    text: str => 待写入的文本\n
    return: str => 临时文件的路径
    """
    with Path(tempfile.gettempdir()).joinpath(file_name).open("w", encoding="utf-8") as fp:
        fp.write(text)
        fname = fp.name
    return fname


# %% ---------------------------------------------------------------------------
# class: InstTbDoc
# ------------------------------------------------------------------------------
class InstTbDoc:
    """
    处理 verilog 文件
    """

    # %% ---------------------------------------------------------------------------
    # 初始化 InstTbDoc, 读取文件并提取需要出来的代码
    # ------------------------------------------------------------------------------
    def __init__(self, file: str) -> None:
        """
        初始化 InstTbDoc, 读取文件并提取需要出来的代码\n
        file: str => verilog 文件路径
        """
        # %% ---------------------------------------------------------------------------
        # init
        # ------------------------------------------------------------------------------
        with open(file, "r", encoding="utf-8") as fp:
            code = fp.read()
        # -------- simplify code --------
        # 删除 [块注释, 无需文档化的整行注释, 空行]
        code, _ = re.subn(r"\s*/\*.*?\*/", "\n", code, flags=re.S)  # 删除块注释
        code, _ = re.subn(r"^\s*//(?!>).*\n", "", code, flags=re.M)  # 删除无需文档化的整行注释
        code, _ = re.subn(r"^(\r)?\n", "", code, flags=re.M)  # 删除空行
        # -------- variables --------
        self.__code = code
        # -------- variables --------
        self.__module_name = ""
        self.__module_parameters = []
        self.__module_ports = []
        self.__comments_list = []
        self.__has_wavedrom = False

    # %% ---------------------------------------------------------------------------
    # 解析代码, 提取 comments, module (name, parameters, ports, descriptions)
    # ------------------------------------------------------------------------------
    def _parse_module(self) -> None:
        """
        解析代码, 提取 module (name, parameters, ports, descriptions)
        """
        # -------- variable --------
        module_name = ""
        parameters = []
        ports = []
        # -------- 简化 code --------
        code_m, _ = re.subn(r"^\s*//.*\n", "", self.__code, flags=re.M)  # 删除整行注释
        code_m, _ = re.subn(r"\(\s*\*.*\*\s*\)\s*", "", code_m)  # 删除属性
        # -------- 提取 module name --------
        tmp_code, _ = re.subn(r"//.*\n", "\n", code_m)  # 删除行尾注释
        if tMatch := re.search(r"module\s*([a-zA-Z_]\w*)\b(.*?;)", tmp_code, re.S):
            module_name = tMatch.group(1)
            module_body = tMatch.group(2)
        else:
            return
        # -------- 提取参数和端口 --------
        tPos = 0
        # 提取 parameters 文本
        if tMatch := re.search(r"#\s*\((.*?)\)", module_body, re.S):
            tPos = tMatch.end()
            param_text = tMatch.group(1)
        else:
            param_text = ""
        # 提取 ports 文本
        if tMatch := re.search(r"\((.*?)\);", module_body[tPos:], re.S):
            port_text = tMatch.group(1)
        else:
            port_text = ""
        # -------- 提取 parameters --------
        if param_text:
            #   获取 parameter 的 [name, type, value]
            for p_type, *rest, p_var in re.findall(
                r"^\s*parameter"
                r"\s*(((signed)?\s*(\[.+:.+\])?)|integer|real|realtime|time)?"  # 1: 类型 (整体); 2: 类型(signed range); 3: singed, 4: range
                r"\s*([a-zA-Z_].*)$",  # 5: name=value
                param_text,
                re.M,
            ):
                p_type, _ = re.subn(r"\s+", " ", p_type)
                for p_name, *rest, p_value in re.findall(r"(\w+)(\s*=\s*(\w+))?", p_var):
                    if not p_value:
                        p_value = ""
                    parameters.append(
                        {
                            "name": p_name,
                            "type": p_type,
                            "value": p_value,
                            "description": "",
                        }
                    )
            #   获取 parameter 的 [description]
            for param in parameters:
                if tMatch := re.search(
                    r"^\s*parameter\b.+\b" + param["name"] + r"\b.*//(.*)\n", code_m, flags=re.M
                ):
                    param["description"] = tMatch.group(1).strip()
        # -------- 提取 ports --------
        if port_text:
            #   获取 port 的 [name, direction, type]
            for port in re.findall(
                r"^\s*(input|output|inout)"  # 1: direction
                r"\s*(wire|wand|wor|tri|tri0|tri1|triand|trior|trireg|reg)?"  # 2: type
                r"\s*(signed)?"  # 3: singed
                r"\s*(\[.+:.+\])?"  # 4: range
                r"\s*([a-zA-Z_].*)$",  # 5: name=value
                port_text,
                re.M,
            ):
                p_direction = port[0]
                p_type = port[1] if port[1] else "(wire)"
                if port[2]:
                    p_type += f" {port[2]}"
                if port[3]:
                    p_type += f" {port[3]}"
                for p_name, *rest in re.findall(r"(\w+)(\s*=\s*(\w+))?", port[4]):
                    ports.append(
                        {
                            "name": p_name,
                            "direction": p_direction,
                            "type": p_type,
                            "description": "",
                        }
                    )
            #   获取 port 的 [description]
            for port in ports:
                if tMatch := re.search(
                    r"^\s*\b" + port["direction"] + r"\b.*\b" + port["name"] + r"\b.*//(.*)\n",
                    code_m,
                    flags=re.M,
                ):
                    port["description"] = tMatch.group(1).strip()
        # -------- 更新数据 --------
        self.__module_name = module_name
        self.__module_parameters = parameters
        self.__module_ports = ports

    # %% ---------------------------------------------------------------------------
    # parse_comment
    # ------------------------------------------------------------------------------
    def _parse_comment(self) -> None:
        """
        解析注释, 从中提取 [wavedrom 数据, table 数据, 普通文字行]
        """
        # -------- 如果没有需要处理的注释 --------
        comments = re.findall(r"^\s*//>(.*\n)", self.__code, re.M)  # 需要文档化的整行注释
        if not comments:
            return
        cmt_items = len(comments)
        # -------- 计算缩进 --------
        def _get_comment_indent(comment_line: str) -> int:
            """
            计算一行注释的缩进 (从"//>" 之后开始)\n
            comment_line: str => 一行注释\n
            return: int => 缩进的字符数
            """
            indent = 0

            for char in comment_line:
                if char == " ":
                    indent += 1
                elif char == "\t":
                    match (indent // 4):
                        case 0:
                            indent += 1
                        case 1:
                            indent += 4
                        case 2:
                            indent += 3
                        case 3:
                            indent += 2
                else:
                    break

            return indent

        # -------- 寻找 wavedrom 数据 --------
        def get_wave(comments: list[str], start: int = 0, stop: int = cmt_items) -> tuple:
            """
            从注释中提取 wavedrom 数据\n
            comments: list[str] => 需要 previes 的注释行\n
            start: int => 搜索的起始索引\n
            stop: int => 搜索的结束索引\n
            return: tuple =>\n
                wavedrom 数据在列表中的起始索引,\n
                wavedrom 数据在列表中的结束索引,\n
                wavedrom 数据: dict =>\n
                    type: str => "WaveDrom",\n
                    data: str of json => 字符表示的 json 数据,\n
                    indent: int => 缩进
            """
            # -------- variable --------
            wave_start = -1
            wave_end = -1
            wave_text = ""
            # -------- 查找 wavedrom --------
            # 找 wave 开头
            for i in range(start, stop):
                text = comments[i]
                if tMatch := re.search(r"<(wave(drom|_ya?ml)?)>", text):
                    wave_start = i
                    wave_key = tMatch.group(1)
                    wave_text += text[tMatch.end() :]
                    indent = _get_comment_indent(text)
                    break
            if wave_start == -1:
                return None
            # 找 wave 文本和结尾
            for i in range(wave_start + 1, stop):
                text = comments[i]
                if tMatch := re.search(f"</{wave_key}>", text):
                    wave_end = i
                    wave_text += text[: tMatch.start()]
                    break
                else:
                    wave_text += text
            if wave_end == -1:
                return None
            # -------- 处理 wavedrom --------
            # 如果找到 <wavedrom> ... </wavedrom>
            if wave_key in ("wave", "wavedrom"):
                wave_text = wave_text.strip()
                try:
                    wave_dict = json.loads(wave_text)
                except json.JSONDecodeError:
                    try:
                        wave_dict = eval(
                            wave_text,
                            type("Dummy", (dict,), dict(__getitem__=lambda s, n: n))(),
                        )
                    except:
                        return None
                except:
                    return None
            # 如果找到 <wave_yaml> ... </wave_yaml>
            elif wave_key in ("wave_yaml", "wave_yml"):
                try:
                    wave_dict = yaml.load(wave_text, yaml.Loader)
                except:
                    return None
            # -------- 返回数据 --------
            return (
                wave_start,
                wave_end,
                {
                    "type": "WaveDrom",
                    "data": json.dumps(wave_dict, ensure_ascii=False),
                    "indent": indent,
                },
            )

        # -------- 寻找 table 数据 --------
        def get_table(comments: list[str], start: int = 0, stop: int = cmt_items) -> tuple:
            """
            从注释中提取 table 数据\n
            comments: list[str] => 需要 preview 的注释行\n
            start: int => 搜索的起始索引\n
            stop: int => 搜索的结束索引\n
            return: tuple =>\n
                table 数据在列表中的起始索引,\n
                table 数据在列表中的结束索引,\n
                table 数据: dict =>\n
                    type: str => "table",\n
                    data: dict => table 数据的各个要素,\n
                        thead: list of str => 表头文本,\n
                        align: list of str => 对齐方式 ("left", "center", "right" 之一),\n
                        tbody: list of list of str => 表格文本\n
                    indent: int => 缩进
            """
            # -------- variable --------
            table_start = -1
            table_end = -1
            # -------- 查找 table --------
            # 找 table 开头
            for i in range(start, stop):
                text = comments[i]
                # 找 table head
                if re.search(r"^[ \t]*(\|)?(.+\|)+.*\n", text, re.M):
                    indent = _get_comment_indent(text)
                else:
                    continue
                # 找 table align
                text = comments[i + 1]
                if (
                    re.search(r"^[ \t]*(\|)?(\s*[:-]-+[-:]\s*\|)+.*\n", text, re.M)
                    and _get_comment_indent(text) == indent
                ):
                    pass
                else:
                    continue
                # 找 table body
                text = comments[i + 2]
                if (
                    re.search(r"^[ \t]*(\|)?(.+\|)+.*\n", text, re.M)
                    and _get_comment_indent(text) == indent
                ):
                    table_start = i
                    table_end = table_start + 2
                    break
                else:
                    continue
            if table_start == -1:
                return None
            # 找 table 剩余的 body
            for i in range(table_start + 3, stop):
                text = comments[i]
                if (
                    re.search(r"^[ \t]*(\|)?(.+\|)+.*\n", text, re.M)
                    and _get_comment_indent(text) == indent
                ):
                    table_end = i
                else:
                    break
            # -------- 处理 table --------
            # 获取表格对齐方式
            def get_align(x):
                if re.match(r":-+:$", x):
                    return "center"
                elif re.match(r"-{2,}:$", x):
                    return "right"
                else:
                    return "left"

            thead = [x.strip(" ") for x in comments[table_start][:-1].split("|")]  # 表头项
            talign = [
                get_align(x.strip(" ")) for x in comments[table_start + 1][:-1].split("|")
            ]  # 对齐方式
            tbody = []
            for i in range(table_start + 2, table_end + 1):
                tbody.append([x.strip(" ") for x in comments[i][:-1].split("|")])
            # -------- 返回数据 --------
            return (
                table_start,
                table_end,
                {
                    "type": "table",
                    "data": {
                        "thead": thead,
                        "align": talign,
                        "tbody": tbody,
                    },
                    "indent": indent,
                },
            )

        # -------- 将每行注释转换成列表 --------
        def get_lines(comments: list[str], start: int = 0, stop: int = cmt_items) -> list[dict]:
            """
            从注释中提取普通行\n
            comments: list[str] => 需要 preview 的注释行\n
            start: int => 搜索的起始索引\n
            stop: int => 搜索的结束索引\n
            return: list[dict] =>\n
                type: str => 章节标题 ("header"), 条目 ("list"), 普通文本 ("normal"),\n
                data: str => 文本,\n
                indent: int => 缩进
            """

            tList = []
            for line in comments[start:stop]:
                indent = _get_comment_indent(line)
                if re.match(r"\s*#\s+.*$", line):  # chapter
                    tList.append(
                        {
                            "type": "header",
                            "data": line,
                            "indent": indent,
                        }
                    )
                elif re.match(r"\s*([\*\+-]|\d+\.)\s+.*$", line):  # list
                    tList.append(
                        {
                            "type": "list",
                            "data": line,
                            "indent": indent,
                        }
                    )
                elif re.match(r"\s*$", line):  # normal
                    pass
                else:
                    tList.append(
                        {
                            "type": "normal",
                            "data": line,
                            "indent": indent,
                        }
                    )
            return tList

        # -------- 解析 comments --------
        tPos = 0
        comments_list = []
        has_wavedrom = False

        while wave_dat := get_wave(comments, tPos):
            has_wavedrom = True
            # 处理 wave 之前的数据
            while table_dat := get_table(comments, tPos, wave_dat[0]):
                # 处理 table 之前的数据
                if tList := get_lines(comments, tPos, table_dat[0]):
                    comments_list += tList
                # 处理 table 数据
                comments_list.append(table_dat[2])
                # 更新 pos
                tPos = table_dat[1] + 1
            # 处理 table 之前的数据
            else:
                if tList := get_lines(comments, tPos, wave_dat[0]):
                    comments_list += tList
            # 处理 wave 数据
            comments_list.append(wave_dat[2])
            # 更新 pos
            tPos = wave_dat[1] + 1
        else:
            # 处理 wave 之后的数据
            while table_dat := get_table(comments, tPos):
                # 处理 table 之前的数据
                if tList := get_lines(comments, tPos, table_dat[0]):
                    comments_list += tList
                # 处理 table 数据
                comments_list.append(table_dat[2])
                # 更新 pos
                tPos = table_dat[1] + 1
            else:
                if tList := get_lines(comments, tPos):
                    comments_list += tList

        # -------- 更新数据 comments --------
        self.__comments_list = comments_list
        self.__has_wavedrom = has_wavedrom

    # %% ---------------------------------------------------------------------------
    # dump 解析数据
    # ------------------------------------------------------------------------------
    def dump_parsed(self):
        text = ""
        # dump module
        text += "# ------------------------------------------------------------------------------\n"
        text += f"module::name = {self.__module_name}\n"
        text += "# ------------------------------------------------------------------------------\n"
        text += f"module::parameters = (see below)\n"
        for p in self.__module_parameters:
            text += f"\t{p}\n"
        text += "# ------------------------------------------------------------------------------\n"
        text += f"module::ports = (see below)\n"
        for p in self.__module_ports:
            text += f"\t{p}\n"
        # dump commenmts
        text += "# ------------------------------------------------------------------------------\n"
        text += f"comments = (see below)\n"
        for c in self.__comments_list:
            text += f"\t{c}\n"
        text += f"comments::has_wavedrom = {self.__has_wavedrom}\n"
        # dump raw::code
        text += "\n\n"
        text += "# ------------------------------------------------------------------------------\n"
        text += f"raw::code = (see below)\n"
        text += f"{self.__code}\n"

        # 写入临时文件
        return write_to_tmpfile("hyhdl_dump", text)

    # %% ---------------------------------------------------------------------------
    # draw the block diagram
    # ------------------------------------------------------------------------------
    def _draw_module_bd(self) -> None:
        """
        绘制 module 的框图
        """
        # -------- 如果没有端口, 不画图 --------
        if self.__module_ports == []:
            return ""
        # -------- 整理数据 --------
        parameters = self.__module_parameters
        ports_left = [x for x in self.__module_ports if x["direction"] == "input"]
        ports_right = [x for x in self.__module_ports if x["direction"] in ("output", "inout")]
        # -------- 获取框图的基本参数 --------
        max_chars_param = (
            max([len(x["name"]) for x in parameters]) if parameters else 0
        )  # parameters 中 name 的最大的字符宽度
        max_chars_port_l = (
            max([len(x["name"]) for x in ports_left]) if ports_left else 0
        )  # 左侧 (in) 端口中 name 的最大字符宽度
        max_chars_port_r = (
            max([len(x["name"]) for x in ports_right]) if ports_right else 0
        )  # 右侧 (out, inout) 端口中 name 的最大字符宽度
        # 框图方框宽度
        rect_width = 30 + 10 * max(max_chars_param, max_chars_port_l + max_chars_port_r)

        max_chars_param = (
            max([len(x["type"]) for x in parameters]) if parameters else 0
        )  # parameters 中 type 的最大的字符宽度
        max_chars_port_l = (
            max([len(x["type"]) for x in ports_left]) if ports_left else 0
        )  # 左侧 (in) 端口中 type 的最大字符宽度
        max_chars_port_r = (
            max([len(x["type"]) for x in ports_right]) if ports_right else 0
        )  # 右侧 (out, inout) 端口中 type 的最大字符宽度
        # 框图边界宽度
        margin_width = 10 * max(max_chars_param, max_chars_port_l, max_chars_port_r) + 10

        # 框图高度 (parameters)
        rect1_height = len(parameters) * 20 + 10 if parameters else 0
        # 框图高度 (ports)
        rect2_height = 10 + 20 * max(len(ports_left), len(ports_right))
        # 框图间距 (parameters vs ports)
        rect2_offset = rect1_height + 10 if rect1_height > 0 else 0
        # -------- 生成 svg 代码 --------
        #   生成 svg 头
        svg_code = (
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            f'viewBox="0 0 {rect_width + margin_width * 2} {rect2_offset + rect2_height}">\n'
        )
        # 绘制 parameters 的图
        if rect1_height > 0:
            # 绘制方框
            svg_code += (
                f'\t<rect x="{margin_width}" y="0" width="{rect_width}" height="{rect1_height}" '
                f'fill="black"></rect>\n'
            )
            svg_code += (
                f'\t<rect x="{margin_width + 2}" y="2" width="{rect_width - 4}" height="{rect1_height - 4}" '
                f'fill="#bdecb6"></rect>\n'
            )
            # 绘制线和文字
            for i, param in enumerate(parameters, 1):
                text_y = i * 20
                line_y = text_y - 5
                svg_code += (
                    f'\t<line x1="{margin_width - 10}" y1="{line_y}" x2="{margin_width}" y2="{line_y}" '
                    f'stroke="black" stroke-width="2"></line>\n'
                )
                svg_code += (
                    f'\t<text x="{margin_width + 5}" y="{text_y}" '
                    f'font-size="18">{param["name"]}</text>\n'
                )
        # 绘制 ports 的图
        #   绘制方框
        svg_code += (
            f'\t<rect x="{margin_width}" y="{rect2_offset}" width="{rect_width}" height="{rect2_height}" '
            f'fill="black"></rect>\n'
        )
        svg_code += (
            f'\t<rect x="{margin_width + 2}" y="{rect2_offset + 2}" width="{rect_width - 4}" height="{rect2_height - 4}" '
            f'fill="#fdfd96"></rect>\n'
        )
        #   绘制左侧线和文字
        for i, port in enumerate(ports_left, 1):
            text_y = i * 20 + rect2_offset
            line_y = text_y - 5
            svg_code += (
                f'\t<line x1="{margin_width - 10}" y1="{line_y}" x2="{margin_width}" y2="{line_y}" '
                f'stroke="black" stroke-width="2"></line>\n'
            )
            svg_code += (
                f'\t<polyline points="'
                f"{margin_width     },{line_y - 5} "
                f"{margin_width + 10},{line_y - 5} "
                f"{margin_width + 15},{line_y    } "
                f"{margin_width + 10},{line_y + 5} "
                f"{margin_width     },{line_y + 5}"
                f'" style="fill:none; stroke:black; stroke-width:2"></polyline>\n'
            )
            svg_code += (
                f'\t<text x="{margin_width + 20}" y="{text_y}" '
                f'font-size="18">{port["name"]}</text>\n'
            )
            svg_code += (
                f'\t<text x="{margin_width - 15}" y="{text_y}" '
                f'text-anchor="end" font-size="18">{port["type"]}</text>\n'
            )
        #   绘制右侧线和文字
        for i, port in enumerate(ports_right, 1):
            x_right = margin_width + rect_width
            text_y = i * 20 + rect2_offset
            line_y = text_y - 5
            svg_code += (
                f'\t<line x1="{x_right}" y1="{line_y}" x2="{x_right + 10}" y2="{line_y}" '
                f'stroke="black" stroke-width="2"></line>\n'
            )
            if port["direction"] == "output":
                svg_code += (
                    f'\t<polyline points="'
                    f"{x_right - 2     },{line_y    } "
                    f"{x_right - 2 -  5},{line_y - 5} "
                    f"{x_right - 2 - 15},{line_y - 5} "
                    f"{x_right - 2 - 15},{line_y + 5} "
                    f"{x_right - 2 -  5},{line_y + 5} "
                    f"{x_right - 2     },{line_y    }"
                    f'" style="fill:none; stroke:black; stroke-width:2"></polyline>\n'
                )
            elif port["direction"] == "inout":
                # if port["direction"] == "output":
                svg_code += (
                    f'\t<polyline points="'
                    f"{x_right - 2     },{line_y    } "
                    f"{x_right - 2 -  5},{line_y - 5} "
                    f"{x_right - 2 - 10},{line_y - 5} "
                    f"{x_right - 2 - 15},{line_y    } "
                    f"{x_right - 2 - 10},{line_y + 5} "
                    f"{x_right - 2 -  5},{line_y + 5} "
                    f"{x_right - 2     },{line_y    }"
                    f'" style="fill:none; stroke:black; stroke-width:2"></polyline>\n'
                )
            svg_code += (
                f'\t<text x="{x_right - 22}" y="{text_y}" '
                f'text-anchor="end" font-size="18">{port["name"]}</text>\n'
            )
            svg_code += (
                f'\t<text x="{x_right + 15}" y="{text_y}" '
                f'font-size="18">{port["type"]}</text>\n'
            )
        # 生成 svg 尾
        svg_code += f"</svg>\n"
        # -------- 更新数据 --------
        return svg_code

    # %% ---------------------------------------------------------------------------
    # 格式化注释 -> html
    # ------------------------------------------------------------------------------
    def _get_notes_html(self) -> str:
        """
        格式化注释, 生成 html\n
        return: str => 由注释转换而来的 html 字符串
        """
        # -------- 如果没有需要处理的 comments_list --------
        if self.__comments_list == []:
            return ""
        comments_list = self.__comments_list
        notes_html = ""
        # -------- 处理 comments_list --------
        for item in comments_list:
            # -------- 预处理 --------
            cmtType = item["type"]
            cmtData = item["data"]
            html_indent = (item["indent"] - 1) // 2 if item["indent"] else 0
            # -------- 转 html --------
            match (cmtType):
                case "WaveDrom":
                    notes_html += (
                        f'<div style="padding: 0 0 50px {html_indent}rem">\n'
                        if html_indent
                        else f'<div style="padding: 0 0 50px">\n'
                    )
                    notes_html += (
                        f'\t<script type="WaveDrom">\n'
                        f"\t\t{cmtData}\n"
                        f"\t</script>\n"
                        f"</div>\n"
                    )
                # 如果是 table
                case "table":
                    # <div>
                    notes_html += (
                        f'<div style="padding-left:{html_indent}rem">\n'
                        if html_indent
                        else f"<div>\n"
                    )
                    #   <table>
                    notes_html += "<table>\n"
                    #       <thead>
                    notes_html += "\t<thead>\n\t\t<tr>\n"
                    for td in cmtData["thead"]:
                        notes_html += f"\t\t\t<th>{td}</th>\n"
                    notes_html += "\t\t</tr>\n\t</thead>\n"
                    #       <tbody>
                    notes_html += "\t<tbody>\n"
                    for tbody in cmtData["tbody"]:
                        notes_html += "\t\t<tr>\n"
                        for tAlign, td_item in zip(cmtData["align"], tbody):
                            if tAlign == "left":
                                notes_html += f"\t\t\t<td>{td_item}</td>\n"
                            else:
                                notes_html += (
                                    f'\t\t\t<td style="text-align: {tAlign}">{td_item}</td>\n'
                                )
                        notes_html += "\t\t</tr>\n"
                    notes_html += "\t</tbody>\n"
                    #   </table>
                    notes_html += "</table>\n"
                    # </div>
                    notes_html += "</div>\n"
                # 如果是 normal
                case _:
                    tStr = cmtData.strip()
                    if tStr:
                        tStr = tStr.replace("<", "&lt;").replace(">", "&gt;")
                        notes_html += (
                            f'<p style="padding-left:{html_indent}rem">{tStr}</p>\n'
                            if html_indent
                            else f"<p>{tStr}</p>\n"
                        )
                    else:
                        notes_html += f"<br>\n"
        # -------- 返回数据 --------
        return notes_html

    # %% ---------------------------------------------------------------------------
    # 生成例化代码
    # ------------------------------------------------------------------------------
    def get_inst(self) -> str:
        """
        生成端口例化代码\n
        return: str => 端口例化代码
        """
        # -------- 整理数据 --------
        self._parse_module()

        module_name = self.__module_name
        parameters = self.__module_parameters
        ports = self.__module_ports

        if (not module_name) or (not ports):
            return ""
        # 输出 module name
        inst = f"    {module_name}"
        # 输出 parameters
        if len(parameters):
            names = [x["name"] for x in parameters]
            get_param_value = lambda x: x["name"] if x["value"] == " " else x["value"]
            values = [get_param_value(x) for x in parameters]
            name_width = ((max(map(len, names)) + 1) // 4) * 4 + 3
            value_width = (max(map(len, values)) // 4) * 4 + 3

            inst += f" # (\n"
            for name, value, p in zip(names[:-1], values, parameters):
                inst += (
                    f"        .{name.ljust(name_width)}({value.ljust(value_width)}),"
                    f'  // {p["description"]}\n'
                )
            inst += (
                f"        .{names[-1].ljust(name_width)}({values[-1].ljust(value_width)}) "
                f'  // {parameters[-1]["description"]}\n'
            )
            inst += f"    )"
        # 输出 instantiation name
        inst += f" u_{module_name} (\n"
        # 输出 ports
        names = [x["name"] for x in ports]
        name_width = ((max(map(len, names)) + 1) // 4) * 4 + 3

        for name, p in zip(names[:-1], ports):
            inst += (
                f"        .{name.ljust(name_width)}({name.ljust(name_width)}),"
                f'  // {p["direction"]}, {p["type"]}, {p["description"]}\n'
            )
        inst += (
            f"        .{names[-1].ljust(name_width)}({names[-1].ljust(name_width)}) "
            f'  // {ports[-1]["direction"]}, {ports[-1]["type"]}, {ports[-1]["description"]}\n'
        )
        inst += f"    );\n"
        # -------- return --------
        return write_to_tmpfile("hyhdl_output", inst)

    # %% ---------------------------------------------------------------------------
    # 生成 testbench
    # ------------------------------------------------------------------------------
    def get_testbench(self, template_fname: str) -> str:
        """
        生成端口例化代码\n
        template_fname: str => testbench template file
        return: str => 端口例化代码
        """
        # -------- 整理数据 --------
        self._parse_module()

        module_name = self.__module_name
        parameters = self.__module_parameters
        ports = self.__module_ports

        if (not module_name) or (not ports):
            return ""
        # -------- 生成 uut 代码 --------
        uut = ""
        # uut += f"    // module instantiation\n"
        # 输出 parameters 的声明
        if len(parameters):
            param_names = [x["name"] for x in parameters]
            values = [x["value"] for x in parameters]
            name_width = ((max(map(len, param_names)) + 2) // 4) * 4 + 2
            value_width = ((max(map(len, values)) + 2) // 4) * 4 + 2

            uut += f"    // parameters\n"
            for p in parameters:
                uut += (
                    f'    parameter {p["name"].ljust(name_width)}= {p["value"].ljust(value_width)};'
                    f'   // {p["description"]}\n'
                )
        # 输出 ports 的声明
        port_names = [x["name"] for x in ports]
        name_width = (max(map(len, port_names)) // 4) * 4 + 4

        def get_port_rng(port_type):
            if tMatch := re.search(r"\[.+:.+\]", port_type, re.S):
                rng, _ = re.subn(r"\s+", " ", tMatch.group(0))
                return rng
            else:
                return ""

        port_rngs = [get_port_rng(x["type"]) for x in ports]
        rng_width = (((max(map(len, port_rngs))) + 1) // 4) * 4 + 2

        uut += "    // ports\n"
        for p, rng in zip(ports, port_rngs):
            if p["direction"] == "input":
                uut += "    reg  "
            else:
                uut += "    wire "
            uut += (
                f'{rng.rjust(rng_width)} {p["name"].ljust(name_width)};'
                f'   // {p["description"]}\n'
            )
        # 输出 module instantiation
        uut += f"    // module\n"
        uut += f"    {module_name}"
        #   输出 parameters
        if len(parameters):
            name_width = ((max(map(len, param_names)) + 1) // 4) * 4 + 3
            if len(parameters):
                uut += f" # (\n"
                for p in param_names[:-1]:
                    uut += f"        .{p.ljust(name_width)}({p.ljust(name_width)}),\n"
                uut += f"        .{param_names[-1].ljust(name_width)}({param_names[-1].ljust(name_width)})\n"
                uut += f"    )"
        #   输出 instantiation name
        uut += f" uut (\n"
        #   输出 ports
        name_width = ((max(map(len, port_names)) + 1) // 4) * 4 + 3
        for name in port_names[:-1]:
            uut += f"        .{name.ljust(name_width)}({name.ljust(name_width)}),\n"
        uut += f"        .{port_names[-1].ljust(name_width)}({port_names[-1].ljust(name_width)})\n"
        uut += f"    );"
        # -------- 更新模板 --------
        if template_fname:
            tPath = Path(template_fname)
            tmpl_dir = tPath.parent
            tmpl_name = tPath.name
        else:
            tmpl_dir = pytools_dir
            tmpl_name = "testbenchTemplate.v"

        env = Environment(loader=FileSystemLoader(tmpl_dir))
        tmpl = env.get_template(tmpl_name)
        text = tmpl.render(
            module_name=module_name,
            uut=uut,
        )
        # -------- return --------
        return write_to_tmpfile("hyhdl_output", text)

    # %% ---------------------------------------------------------------------------
    # 生成预览用的 html
    # ------------------------------------------------------------------------------
    def get_preview_html(self) -> str:
        """
        生成预览用的 html\n
        return: str => html 的路径
        """
        # -------- 整理数据 --------
        self._parse_module()
        self._parse_comment()
        wavedrom_js_path = VS_EXT_PATH_PREFIX + quote(  # 需要使用 vscode 的安全协议
            pytools_dir.joinpath("wavedrom", "wavedrom.min.js").as_posix()
        )
        wavedrom_theme_path = VS_EXT_PATH_PREFIX + quote(  # 需要使用 vscode 的安全协议
            pytools_dir.joinpath("wavedrom", "default.js").as_posix()
        )
        # print(f"{wavedrom_js_path=}")
        # print(f"{wavedrom_theme_path=}")
        module_name = self.__module_name
        module_diagram = self._draw_module_bd()
        parameters = self.__module_parameters
        ports = self.__module_ports
        notes_html = self._get_notes_html()
        # -------- 替换模板 --------
        env = Environment(loader=FileSystemLoader(pytools_dir))
        tmpl = env.get_template("previewTemplate.html")
        text = tmpl.render(
            hasWavedrom=self.__has_wavedrom,
            wavedrom_js_path=wavedrom_js_path,
            wavedrom_theme_path=wavedrom_theme_path,
            module_name=module_name,
            module_diagram=module_diagram,
            parameters=parameters,
            hasParameters=len(parameters) > 0,
            ports=ports,
            hasPorts=len(ports) > 0,
            notes_html=notes_html,
        )
        # -------- 写入临时文件 --------
        return write_to_tmpfile("hyhdl_output", text)

    # %% ---------------------------------------------------------------------------
    # 生成导出用的 html
    # ------------------------------------------------------------------------------
    def get_export_html(self) -> str:
        """
        生成导出用的 html\n
        return: str => html 的路径
        """
        # -------- 整理数据 --------
        self._parse_module()
        self._parse_comment()

        module_name = self.__module_name
        module_diagram = self._draw_module_bd()
        parameters = self.__module_parameters
        ports = self.__module_ports
        notes_html = self._get_notes_html()
        # -------- 替换模板 --------
        env = Environment(loader=FileSystemLoader(pytools_dir))
        tmpl = env.get_template("exportTemplate.html")
        text = tmpl.render(
            hasWavedrom=self.__has_wavedrom,
            module_name=module_name,
            module_diagram=module_diagram,
            parameters=parameters,
            hasParameters=len(parameters) > 0,
            ports=ports,
            hasPorts=len(ports) > 0,
            notes_html=notes_html,
        )
        # -------- 写入临时文件 --------
        return write_to_tmpfile("hyhdl_output", text)


# %% ---------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------
def main(option, fname, template_fname=None):
    myDoc = InstTbDoc(fname)

    if option == "-i":  # for instantiation
        tmpf = myDoc.get_inst()
    elif option == "-t":  # for instantiation
        tmpf = myDoc.get_testbench(template_fname)
    elif option == "-p":  # for preview
        tmpf = myDoc.get_preview_html()
    elif option == "-h":  # for export html
        tmpf = myDoc.get_export_html()

    print(tmpf, end=None)
    # ! debug start
    myDoc.dump_parsed()
    # ! debug end


# %%
if __name__ == "__main__":
    pytools_dir = Path(sys.argv[0]).absolute().parent

    def show_error(message: str):
        """
        使用 stderr 通道显示错误信息\n
        message:str => 要显示的错误信息
        """
        raise Warning(message)

    match (len(sys.argv)):
        case 2:  # exe + opt
            opt = sys.argv[1].strip()
            fname = Path(tempfile.gettempdir()).joinpath("code")

            if opt not in ("-i", "-t", "-p", "-h"):
                show_error(USAGE_TIPS)
            elif not Path(fname).exists():
                raise FileNotFoundError(fname)
                # show_error(f"the path is not exists")
            else:
                main(opt, fname)
        case 3:  # exe + opt + path
            opt = sys.argv[1].strip()
            fname = sys.argv[2].strip()

            if opt not in ("-i", "-t", "-p", "-h"):
                show_error(USAGE_TIPS)
            elif not Path(fname).exists():
                raise FileNotFoundError(fname)
                # show_error(f"the path is not exists")
            else:
                main(opt, fname)
        case 4:  # exe + opt + `-T` + `testbench_template_path`
            opt = sys.argv[1].strip()
            fname = Path(tempfile.gettempdir()).joinpath("code")
            opt2 = sys.argv[2].strip()
            template_fname = sys.argv[3].strip()

            if opt not in ("-i", "-t", "-p", "-h"):
                show_error(USAGE_TIPS)
            elif opt2 != "-T":
                show_error(USAGE_TIPS)
            elif not Path(template_fname).exists():
                raise FileNotFoundError(template_fname)
                # show_error(f"the path of the file of testbench_template is not exists")
            else:
                main(opt, fname, template_fname)
        case 5:  # exe + opt + path + `-T` + `testbench_template_path`
            opt = sys.argv[1].strip()
            fname = sys.argv[2].strip()
            opt2 = sys.argv[3].strip()
            template_fname = sys.argv[4].strip()

            if opt not in ("-i", "-t", "-p", "-h"):
                show_error(USAGE_TIPS)
            elif not Path(fname).exists():
                raise FileNotFoundError(fname)
                # show_error(f"the path is not exists")
            elif opt2 != "-T":
                show_error(USAGE_TIPS)
            elif not Path(template_fname).exists():
                raise FileNotFoundError(template_fname)
                # show_error(f"the path of the file of testbench_template is not exists")
            else:
                main(opt, fname, template_fname)
        case _:
            show_error(USAGE_TIPS)
