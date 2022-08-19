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
        # -------- 思路 --------
        # 需要的信息: module name, parameter 信息, port 信息
        #   parameters: list[dict] => 所有必要的信息
        #       parameter 条目: dict(name:str = xx, type:str = xx, value:str = xx, description:str = xx)
        #   ports: list[dict] => 所有必要的信息
        #       port 条目: dict(name:str = xx, direction:str = xx, type:str = xx, description:str = xx)
        # 处理方法
        #   1. 删除注释, 以避免干涉解析
        #   2. 分离 module name 和 body
        #   3. 从 body 中提取 parameters declaration 和 ports declaration
        #   4. 提取 parameter item
        #   5. 提取 ports item

        # -------- 简化 code --------
        code_m = clean_comment_keep_eol(self.__code)
        code_m = clean_attribute(code_m)
        code_m_stub = clean_comment_all(code_m)
        # -------- 提取 module name 和 body --------
        re_module = re.compile(
            r"module\s*(?P<name>[a-zA-Z_]\w*)\b(?P<body>.*?;)", re.S
        )  # module statement 文本, 需先删除所有注释和属性
        if m := re_module.search(code_m_stub):
            module_name = m.group("name")
            module_body = m.group("body")
        # -------- 判断 module 声明的有效性 --------
        if not m or not module_name:  # 没有匹配到 module 或 module 没有 name
            self.module_name = ""
            self.module_parameters = []
            self.module_ports = []
            return
        elif not module_body:  # 如果没有匹配到 body
            self.module_name = module_name
            self.module_parameters = []
            self.module_ports = []
            return
        # -------- 提取 parameters and ports --------
        parameters = []
        ports = []
        # -------- re --------
        re_param_port_text = re.compile(
            # r"#\s*\((?P<param_text>.*?)\)(?:\s*\(\s*.+?\)\s*;)",
            r"(#\s*\((?P<param>.*?)\))?"  # parameter declarations
            r"\s*\(\s*(?P<port>(input|output|inout).+?)\)\s*;",  # port declarations
            re.S,
        )  # parameters statement 文本, 需先删除所有注释和属性
        re_param_item = re.compile(
            r"parameter"  # keyword
            r"\s*(?P<type>((?P<signed>signed)?\s*(?P<range>\[[^:]+:[^:]+\])?)|integer|real|realtime|time)?"  # type
            r"\s*(?P<var>[a-zA-Z_]\w*)"  # variable
            r"\s*(=\s*(?P<value>.+?))?"  # value
            r"\s*(,(?=\s*parameter)|\Z)",  # separator
            re.S,
        )
        # parameter_declaration ::= parameter [ signed ] [ range ] list_of_param_assignments ;
        #                         | parameter integer list_of_param_assignments ;
        #                         | parameter real list_of_param_assignments ;
        #                         | parameter realtime list_of_param_assignments ;
        #                         | parameter time list_of_param_assignments ;
        re_port_item = re.compile(
            r"(?P<direction>input|output|inout)"  # direction
            r"\s*(?P<type>wire|wand|wor|tri|tri0|tri1|triand|trior|trireg|reg)?"  # type
            r"\s*(?P<signed>signed)?"  # singed
            r"\s*(?P<range>\[[^:]+:[^:]+\])?"  # range
            r"\s*(?P<var>[a-zA-Z_]\w*)"  # variable
            r"\s*(=\s*(?P<value>.+?))?"  # value
            r"\s*(,(?=\s*(input|output|inout))|\Z)",  # separator
            re.S,
        )
        # inout_declaration ::= inout [ net_type ] [ signed ] [ range ] list_of_port_identifiers
        # input_declaration ::= input [ net_type ] [ signed ] [ range ] list_of_port_identifiers
        # output_declaration ::= output [ net_type ] [ signed ] [ range ] list_of_port_identifiers
        #                      | output [ reg ] [ signed ] [ range ] list_of_port_identifiers
        #                      | output reg [ signed ] [ range ] list_of_variable_port_identifiers
        #                      | output [ output_variable_type ] list_of_port_identifiers
        #                      | output output_variable_type list_of_variable_port_identifiers
        # -------- 提取参数和端口的文本 --------
        if m := re_param_port_text.search(module_body):
            param_text = m.group("param")
            port_text = m.group("port")
            # -------- 提取 parameters --------
            if param_text:
                # 获取 parameter 的 [name, type, value]
                for m in re_param_item.finditer(param_text):
                    parameters.append(
                        {
                            "name": m.group("var"),
                            "type": shorten_spaces(m.group("type")),
                            "value": m.group("value"),
                            "description": "",
                        }
                    )
                # 获取 parameter 的 [description]
                for param in parameters:
                    if m := re.search(
                        r"parameter\b.+\b" + param["name"] + r"\b.*//\s*(?P<d>.*)\s*\n", code_m
                    ):
                        param["description"] = m.group("d")
            # -------- 提取 ports --------
            if port_text:
                # 获取 port 的 [name, direction, type]
                for m in re_port_item.finditer(port_text):
                    if t := m.group("type"):
                        p_type = t
                    else:
                        p_type = "(wire)"
                    if t := m.group("signed"):
                        p_type = f" {t}"
                    if t := m.group("range"):
                        t = shorten_spaces(t)
                        p_type = f" {t}"
                    #
                    ports.append(
                        {
                            "name": m.group("var"),
                            "direction": m.group("direction"),
                            "type": p_type,
                            "description": "",
                        }
                    )
                # 获取 port 的 [description]
                for port in ports:
                    if m := re.search(
                        r"\b" + port["direction"] + r"\b"  # direction
                        r".*"
                        r"\b" + port["name"] + r"\b"  # name
                        r".*//\s*(?P<d>.*)\s*\n",
                        code_m,
                    ):
                        port["description"] = m.group("d")
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
        # -------- 提取需要 documentation 的注释 --------
        cmt_lines = get_comment_doc(self.__code)  # 需要文档化的整行注释
        if not cmt_lines:
            self.comment_items = []
            self.has_wavedrom = False
            return
        # -------- 处理注释 --------
        # -------- variable --------
        comment_items = []
        has_wavedrom = False
        cmt_line_tot = len(cmt_lines)
        # -------- re --------
        re_wave_token_start = re.compile(r"<(?P<token>wave(drom|_ya?ml)?)>")
        re_wave_token_end = re.compile(r"</(?P<token>wave\w*)>")
        re_table_head = re.compile(r"^[ \t]*(\|)?(.+?(?<!\\)\|)+.*$", re.M)
        re_table_align = re.compile(r"^[ \t]*(\|)?(\s*[:-]-+[-:]\s*(?<!\\)\|)+.*$", re.M)
        re_table_body = re.compile(r"^[ \t]*(\|)?(.+?(?<!\\)\|)+.*$", re.M)
        re_table_item_split = re.compile(r"(?<!\\)\|")
        re_line_chapter = re.compile(r"\s*#\s+.*$")
        re_line_list = re.compile(r"\s*([\*\+-]|\d+\.)\s+.*$")
        re_line_empty = re.compile(r"\s*$")
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
                if m := re_wave_token_start.search(text):
                    wave_start = i
                    wave_token = m.group("token")
                    indent = get_doc_indent(text)
                    wave_text += text[m.end() :]
                    break
            else:
                return None
            # 找 wave 文本和结尾
            for i in range(wave_start + 1, stop):
                text = cmt_lines[i]
                if m := re_wave_token_end.search(text):
                    wave_end = i
                    wave_text += text[indent : m.start()]
                    break
                else:
                    wave_text += text[indent:] + "\n"
            else:
                return None
            # -------- 处理 wavedrom --------
            # 如果找到 <wavedrom> ... </wavedrom>
            if wave_token in ("wave", "wavedrom"):
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
            elif wave_token in ("wave_yaml", "wave_yml"):
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
                if re_table_head.search(text):
                    indent = get_doc_indent(text)
                else:
                    continue
                # 找 table align
                text = cmt_lines[i + 1]
                if re_table_align.search(text) and get_doc_indent(text) == indent:
                    pass
                else:
                    continue
                # 找 table body
                text = cmt_lines[i + 2]
                if re_table_body.search(text) and get_doc_indent(text) == indent:
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
                if re_table_body.search(text) and get_doc_indent(text) == indent:
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

            thead = [x.strip(" ") for x in re_table_item_split.split(cmt_lines[table_start])]  # 表头项
            talign = [
                get_align(x.strip(" "))  # 获取对齐方式
                for x in re_table_item_split.split(cmt_lines[table_start + 1])
            ]  # 对齐方式
            tbody = []
            for i in range(table_start + 2, table_end + 1):
                tbody.append([x.strip(" ") for x in re_table_item_split.split(cmt_lines[i])])
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
            # -------- variable --------
            tList = []
            # -------- 处理 --------
            for line in cmt_lines[start:stop]:
                indent = get_doc_indent(line)
                tList.append(
                    {
                        "type": "normal",
                        "data": line,
                        "indent": indent,
                    }
                )
            # -------- return --------
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
