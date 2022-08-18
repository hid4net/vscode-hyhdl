# ==============================================================================
# COPYRIGHT(C) SIAT
# AUTHOR: WangXH<xh.wang@siat.ac.cn>, From the group of PET
# DESCRIPTION:
# *
#
# MODIFICATION HISTORY:---------------------------------------------------------
#    Version | Author       | Date       | Changes
#    :-----: | :----------: | :--------: | -------------------------------------
#    0.1     | WangXH       | 2022-08-14 | start coding
#
# ==============================================================================
# %% ---------------------------------------------------------------------------
# import
# ------------------------------------------------------------------------------
import json
import re

import yaml

from .util_code import *
from .util_file import write_to_tmpfile


# %% ---------------------------------------------------------------------------
# VerilogParser
# ------------------------------------------------------------------------------
class VerilogParser:
    """
    处理 verilog 文件
    """

    # ------------------------------------------------------------------------------
    # 初始化 VerilogParser, 读取文件并提取需要出来的代码
    # ------------------------------------------------------------------------------
    def __init__(self, vlg_file: str) -> None:
        """
        初始化 VerilogParser, 读取文件并提取需要出来的代码\n
        vlg_file: str => verilog 文件路径
        """
        # -------- 读取代码 --------
        with open(vlg_file, "r", encoding="utf-8") as fp:
            code = fp.read()
        # -------- variables --------
        self.__code = code

    # ------------------------------------------------------------------------------
    # 解析代码, 提取 module (name, parameters, ports, descriptions)
    # ------------------------------------------------------------------------------
    def parse_module(self) -> None:
        """
        解析代码, 提取 module (name, parameters, ports, descriptions)
        """
        # -------- variable --------
        module_name = ""
        parameters = (
            []
        )  # list[param_item], 其中 param_item = dict(name:str = xx, type:str = xx, value:str = xx, description:str = xx)
        ports = (
            []
        )  # list[port_item], 其中 port_item = dict(name:str = xx, direction:str = xx, type:str = xx, description:str = xx)
        # -------- re --------
        re_module = re.compile(
            r"module\s*(?P<name>[a-zA-Z_]\w*)\b(?P<body>.*?;)", re.S
        )  # module statement 文本, 需先删除所有注释和属性
        re_params_text = re.compile(
            # r"#\s*\((?P<param_text>.*?)\)(?:\s*\(\s*.+?\)\s*;)",
            r"#\s*\((?P<param_text>.*?)\)" r"(?:\s*\(\s*(input|output|inout).+?\)\s*;)",
            re.S,
        )  # parameters statement 文本, 需先删除所有注释和属性
        re_param_item = re.compile(
            r"^\s*parameter"
            r"\s*(((signed)?\s*(\[.+:.+\])?)|integer|real|realtime|time)?"  # 1: 类型 (整体); 2: 类型(signed range); 3: singed, 4: range
            r"\s*([a-zA-Z_].*)\n",  # 5: name=value
            re.M,
        )
        re_ports_text = re.compile(
            r"\((\s*(input|output|inout).+)\)\s*;", re.S
        )  # ports statement 文本, 需先删除所有注释和属性
        re_port_item = re.compile(
            r"^\s*(input|output|inout)"  # 1: direction
            r"\s*(wire|wand|wor|tri|tri0|tri1|triand|trior|trireg|reg)?"  # 2: type
            r"\s*(signed)?"  # 3: singed
            r"\s*(\[.+:.+\])?"  # 4: range
            r"\s*([a-zA-Z_].*)$",  # 5: name=value
            re.M,
        )
        re_var_value = re.compile(r"(?P<var>\w+)(\s*=\s*(?P<value>(\".*\")|([^\s,]+)))?")
        # -------- 简化 code --------
        code_m = clean_commemt(self.__code, "blk")
        code_m = clean_commemt(code_m, "lnf")
        code_m = clean_attribute(code_m)
        # -------- 提取 module name --------
        if m := re_module.search(clean_commemt(code_m, "lnt")):
            module_name = m.group(1)
            module_body = m.group(2)
        else:
            return
        # -------- 提取参数和端口的文本 --------
        pos = 0
        # 提取 parameters 文本
        if m := re_params_text.search(module_body):
            param_text = m.group(1)
            pos = m.end(1)
        else:
            param_text = ""
        # 提取 ports 文本
        if m := re_ports_text.search(module_body[pos:]):
            port_text = m.group(1)
        else:
            port_text = ""
        # -------- 提取 parameters --------
        if param_text:
            #   获取 parameter 的 [name, type, value]
            for p_type, *a, p_var_val in re_param_item.findall(param_text):
                p_type = p_type.strip()
                for p_name, a, p_value, *b in re_var_value.findall(p_var_val):
                    # if not p_value:
                    #     p_value = ""
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
                if m := re.search(
                    r"^\s*parameter\b.+\b" + param["name"] + r"\b.*//\s*(.*)\n", code_m, flags=re.M
                ):
                    param["description"] = m.group(1)
        # -------- 提取 ports --------
        if port_text:
            #   获取 port 的 [name, direction, type]
            for port in re_port_item.findall(port_text):
                p_direction = port[0]
                p_type = port[1] if port[1] else "(wire)"
                if port[2]:
                    p_type += f" {port[2]}"
                if port[3]:
                    p_type += f" {port[3]}"
                for p_name, a, p_value, *b in re_var_value.findall(port[4]):
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
                if m := re.search(
                    r"^\s*\b" + port["direction"] + r"\b.*\b" + port["name"] + r"\b.*//\s*(.*)\n",
                    code_m,
                    flags=re.M,
                ):
                    port["description"] = m.group(1)
        # -------- 更新数据 --------
        self.module_name = module_name
        self.module_parameters = parameters
        self.module_ports = ports

    # ------------------------------------------------------------------------------
    # parse_comment
    # ------------------------------------------------------------------------------
    def parse_comment(self) -> None:
        """
        解析注释, 从中提取 [wavedrom 数据, table 数据, 普通文字行]
        """
        # -------- variable --------
        comment_items = []
        has_wavedrom = False
        # -------- 如果没有需要处理的注释 --------
        cmt_lines = re_cmt_line_doc.findall(self.__code)  # 需要文档化的整行注释
        if not cmt_lines:
            return
        cmt_line_tot = len(cmt_lines)
        # -------- 计算缩进 --------
        def get_doc_indent(text):
            return get_indent(text, 3) - 3

        # -------- 寻找 wavedrom 数据 --------
        def get_wave(cmt_lines: list[str], start: int = 0, stop: int = cmt_line_tot) -> tuple:
            """
            从注释中提取 wavedrom 数据\n
            cmt_lines: list[str] => 需要 previes 的注释行\n
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
                text = cmt_lines[i]
                if m := re.search(r"<(wave(drom|_ya?ml)?)>", text):
                    wave_start = i
                    wave_key = m.group(1)
                    wave_text += text[m.end() :]
                    indent = get_doc_indent(text)
                    break
            if wave_start == -1:
                return None
            # 找 wave 文本和结尾
            for i in range(wave_start + 1, stop):
                text = cmt_lines[i]
                if m := re.search(f"</{wave_key}>", text):
                    wave_end = i
                    wave_text += text[: m.start()]
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
        def get_table(cmt_lines: list[str], start: int = 0, stop: int = cmt_line_tot) -> tuple:
            """
            从注释中提取 table 数据\n
            cmt_lines: list[str] => 需要 preview 的注释行\n
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
                text = cmt_lines[i]
                # 找 table head
                if re.search(r"^[ \t]*(\|)?(.+\|)+.*\n", text, re.M):
                    indent = get_doc_indent(text)
                else:
                    continue
                # 找 table align
                text = cmt_lines[i + 1]
                if (
                    re.search(r"^[ \t]*(\|)?(\s*[:-]-+[-:]\s*\|)+.*\n", text, re.M)
                    and get_doc_indent(text) == indent
                ):
                    pass
                else:
                    continue
                # 找 table body
                text = cmt_lines[i + 2]
                if (
                    re.search(r"^[ \t]*(\|)?(.+\|)+.*\n", text, re.M)
                    and get_doc_indent(text) == indent
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
                text = cmt_lines[i]
                if (
                    re.search(r"^[ \t]*(\|)?(.+\|)+.*\n", text, re.M)
                    and get_doc_indent(text) == indent
                ):
                    table_end = i
                else:
                    break
            # -------- 处理 table --------
            # 获取表格对齐方式
            def get_align(x):
                if re.fullmatch(r":-+:$", x):
                    return "center"
                elif re.fullmatch(r"-{2,}:$", x):
                    return "right"
                else:
                    return "left"

            thead = [x.strip(" ") for x in cmt_lines[table_start][:-1].split("|")]  # 表头项
            talign = [
                get_align(x.strip(" ")) for x in cmt_lines[table_start + 1][:-1].split("|")
            ]  # 对齐方式
            tbody = []
            for i in range(table_start + 2, table_end + 1):
                tbody.append([x.strip(" ") for x in cmt_lines[i][:-1].split("|")])
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
        def get_lines(cmt_lines: list[str], start: int = 0, stop: int = cmt_line_tot) -> list[dict]:
            """
            从注释中提取普通行\n
            cmt_lines: list[str] => 需要 preview 的注释行\n
            start: int => 搜索的起始索引\n
            stop: int => 搜索的结束索引\n
            return: list[dict] =>\n
                type: str => 章节标题 ("header"), 条目 ("list"), 普通文本 ("normal"),\n
                data: str => 文本,\n
                indent: int => 缩进
            """

            tList = []
            for line in cmt_lines[start:stop]:
                indent = get_doc_indent(line)
                if re.fullmatch(r"\s*#\s+.*$", line):  # chapter
                    tList.append(
                        {
                            "type": "header",
                            "data": line,
                            "indent": indent,
                        }
                    )
                elif re.fullmatch(r"\s*([\*\+-]|\d+\.)\s+.*$", line):  # list
                    tList.append(
                        {
                            "type": "list",
                            "data": line,
                            "indent": indent,
                        }
                    )
                elif re.fullmatch(r"\s*$", line):  # normal
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

        # -------- 解析 cmt_lines --------
        cmt_line_idx = 0
        while wave_dat := get_wave(cmt_lines, cmt_line_idx):
            has_wavedrom = True
            # 处理 wave 之前的数据
            while table_dat := get_table(cmt_lines, cmt_line_idx, wave_dat[0]):
                # 处理 table 之前的数据
                if tList := get_lines(cmt_lines, cmt_line_idx, table_dat[0]):
                    comment_items += tList
                # 处理 table 数据
                comment_items.append(table_dat[2])
                # 更新 cmt_line_idx
                cmt_line_idx = table_dat[1] + 1
            # 处理 table 之前的数据
            else:
                if tList := get_lines(cmt_lines, cmt_line_idx, wave_dat[0]):
                    comment_items += tList
            # 处理 wave 数据
            comment_items.append(wave_dat[2])
            # 更新 cmt_line_idx
            cmt_line_idx = wave_dat[1] + 1
        else:
            # 处理 wave 之后的数据
            while table_dat := get_table(cmt_lines, cmt_line_idx):
                # 处理 table 之前的数据
                if tList := get_lines(cmt_lines, cmt_line_idx, table_dat[0]):
                    comment_items += tList
                # 处理 table 数据
                comment_items.append(table_dat[2])
                # 更新 cmt_line_idx
                cmt_line_idx = table_dat[1] + 1
            else:
                if tList := get_lines(cmt_lines, cmt_line_idx):
                    comment_items += tList

        # -------- 更新数据 cmt_lines --------
        self.comment_items = comment_items
        self.has_wavedrom = has_wavedrom

    # ------------------------------------------------------------------------------
    # dump 解析数据
    # ------------------------------------------------------------------------------
    def dump_parsed(self, dump_module=True, dump_comment=False):
        text = ""
        # dump module
        if dump_module:
            text += (
                "# ------------------------------------------------------------------------------\n"
            )
            text += f"module::name = {self.module_name}\n"
            text += (
                "# ------------------------------------------------------------------------------\n"
            )
            text += f"module::parameters = (see below)\n"
            for p in self.module_parameters:
                text += f"\t{p}\n"
            text += (
                "# ------------------------------------------------------------------------------\n"
            )
            text += f"module::ports = (see below)\n"
            for p in self.module_ports:
                text += f"\t{p}\n"
        # dump commenmts
        if dump_comment:
            text += (
                "# ------------------------------------------------------------------------------\n"
            )
            text += f"cmt_lines = (see below)\n"
            for c in self.comment_items:
                text += f"\t{c}\n"
            text += f"cmt_lines::has_wavedrom = {self.has_wavedrom}\n"
        # dump raw::code
        text += "\n\n"
        text += "# ------------------------------------------------------------------------------\n"
        text += f"raw::verilog_code = (see below)\n"
        text += f"{self.__code}\n"

        # 写入临时文件
        return write_to_tmpfile("hyhdl_dump", text)
