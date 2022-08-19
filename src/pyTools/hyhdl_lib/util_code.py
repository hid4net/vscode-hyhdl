# ==============================================================================
# COPYRIGHT(C) SIAT
# AUTHOR: WangXH<xh.wang@siat.ac.cn>, From the group of PET
# DESCRIPTION:
# *
#
# MODIFICATION HISTORY:---------------------------------------------------------
#    Version | Author       | Date       | Changes
#    :-----: | :----------: | :--------: | -------------------------------------------
#    0.1     | WangXH       | 2022-08-14 | start coding
#
# ==============================================================================
# %% ---------------------------------------------------------------------------
# import
# ------------------------------------------------------------------------------
import re

# %% ---------------------------------------------------------------------------
# 与 verilog 相关的正则表达式常量
# ------------------------------------------------------------------------------
# -------- 注释 --------
# 参考: re.compile(r'//.*?$|/\*.*?\*/|\(\s*(\*)\s*\)|\(\*.*?\*\)|"(?:\\.|[^\\"])*"', re.S | re.M)
re_comment = re.compile(
    r"(?P<cmt_d>^\s*//>.*?$)|"  # 全行注释: 需要 documentation, 优先级: 0 (最高)
    r"(?P<cmt_D>^\s*//(?!>).*?$)|"  # 全行注释: 无需 documentation, 优先级: 0 (最高)
    r"(?P<cmt_eol>//.*?$)|"  # 行尾注释, 优先级: 1
    r"(?P<block>/\*.*?\*/)|"  # 块注释, 优先级: 2
    r'(?P<string>(?<!\\)".*?(?<!\\)")',  # 字符串, 防止字符串中的注释符号影响匹配, 优先级: 3
    re.S | re.M,
)  # 匹配顺序不能随意调换
# -------- attribute --------
# 参考: re.compile(r'//.*?$|/\*.*?\*/|\(\s*(\*)\s*\)|\(\*.*?\*\)|"(?:\\.|[^\\"])*"', re.S | re.M)
re_attribute = re.compile(
    r"(?P<attr>\(\*.*?\*\))|"  # attribute
    r'(?P<string>(?<!\\)".*?(?<!\\)")',  # 字符串, 防止字符串中的 attribute 干扰匹配
    re.S,
)
# -------- blank --------
# re_empty_line = re.compile(r"^\r?\n", re.M)  # 空行

# %% ---------------------------------------------------------------------------
# 删除注释
# ------------------------------------------------------------------------------
def clean_comment_all(text: str) -> str:
    """删除 verilog 代码中所有的注释
    text: str => verilog 代码\n
    return: str => 处理后的代码"""
    # def replacer(m:re.Match) -> str:
    #     if m.group("string"):
    #         return m.group("string")
    #     else:
    #         return ""
    return re_comment.sub(
        lambda m: m.group(0) if m.group("string") else "",
        text,
    )


def clean_comment_keep_eol(text: str) -> str:
    """删除 verilog 代码中所有的注释
    text: str => verilog 代码\n
    return: str => 处理后的代码"""
    # def replacer(m:re.Match) -> str:
    #     if m.group("string") or m.group("cmt_eol"):
    #         return m.group(0)
    #     else:
    #         return ""
    return re_comment.sub(
        lambda m: m.group(0) if m.group("string") or m.group("cmt_eol") else "",
        text,
    )


# %% ---------------------------------------------------------------------------
# 删除 attribute
# ------------------------------------------------------------------------------
def clean_attribute(text: str) -> str:
    """删除 verilog 代码中所有 attribute
    text: str => verilog 代码\n
    return: str => 处理后的代码"""
    return re_attribute.sub(
        lambda m: m.group(0) if m.group("string") else " ",
        text,
    )


# %% ---------------------------------------------------------------------------
# 获取需要 documentation 的注释
# ------------------------------------------------------------------------------
def get_comment_doc(text: str) -> list[str]:
    """获取 verilog 代码中需要 documentation 的行注释
    text: str => verilog 代码\n
    return: list[str] => 匹配到的行注释的列表"""
    return [x[0][3:] for x in re_comment.findall(text) if x[0]]


# %% ---------------------------------------------------------------------------
# 缩短词间空格
# ------------------------------------------------------------------------------
def shorten_spaces(text: str) -> str:
    """缩短所有空白为一个空格
    text: str => verilog 代码\n
    return: str => 处理后的代码"""
    return re.sub("\s+", " ", text)

# %% ---------------------------------------------------------------------------
# 计算缩进
# ------------------------------------------------------------------------------
def get_indent(text: str, offset: int = 0, tab_width: int = 4) -> int:
    """计算一行注释的缩进 (从"//>" 之后开始)\n
    text: str => 文本\n
    offset: int => 文本首字符的偏移\n
    tab_width: int => tab 的字符宽度\n
    return: int => 缩进的字符数
    """
    indent = offset
    for char in text:
        if char == " ":
            indent += 1
        elif char == "\t":
            indent += tab_width - indent % tab_width
        else:
            break
    return indent


# %% ---------------------------------------------------------------------------
# 计算缩进级别
# ------------------------------------------------------------------------------
def get_indent_level(text: str, tab_width: int = 4) -> int:
    return get_indent(text, tab_width=tab_width) // tab_width


#%%
