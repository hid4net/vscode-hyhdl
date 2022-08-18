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
re_cmt_block = re.compile(r"/\*.*?\*/", re.S)  # 块注释
re_cmt_line_whole = re.compile(r"^\s*//.*\n", re.M)  # 整行注释
re_cmt_line_tail = re.compile(r"\s*//.*\n")  # 行尾注释
re_cmt_line_doc = re.compile(r"^\s*//>(.*\n)", re.M)  # 需要 documentation 的注释
re_cmt_line_nodoc = re.compile(r"^\s*//(?!>).*\n", re.M)  # 无需 documentation 的注释
# -------- attribute --------
re_attribute = re.compile(r"\(\s*\*.*\*\s*\)\s*")  # attribute
# -------- empty line --------
# re_empty_line = re.compile(r"^\r?\n", re.M)  # 空行

# %% ---------------------------------------------------------------------------
# 删除注释
# ------------------------------------------------------------------------------
def clean_commemt(text: str, cmtype: str) -> str:
    """
    删除注释\n
    text: str => 输入文本\n
    cmtype: str => 指定注释类型:\n
        'all': 所有注释\n
        'blk': 块注释\n
        'lnf': 行注释 (整行)\n
        'lnt': 行注释 (行尾)\n
        'lnd': 行注释 (需要 documentation 的行注释)\n
        'lnD': 行注释 (无需 documentation 的行注释)\n
    return: str => 处理后的文本
    """
    rslt = text
    match cmtype:
        case "all":
            rslt = re_cmt_block.sub("", text)  # 删除块注释
            rslt = re_cmt_line_tail.sub("\n", text)  # 删除行尾注释
        case "blk":
            rslt = re_cmt_block.sub("", text)  # 删除块注释
        case "lnf":
            rslt = re_cmt_line_whole.sub("", text)  # 删除整行注释
        case "lnt":
            rslt = re_cmt_line_tail.sub("\n", text)  # 删除行尾注释
        case "lnd":
            rslt = re_cmt_line_doc.sub("", text)  # 删除无需文档化的整行注释
        case "lnD":
            rslt = re_cmt_line_nodoc.sub("", text)  # 删除无需文档化的整行注释
    return rslt


# %% ---------------------------------------------------------------------------
# 删除 attribute
# ------------------------------------------------------------------------------
def clean_attribute(text: str) -> str:
    """
    删除 attribute\n
    text: str => 输入文本\n
    return: str => 处理后的文本
    """
    return re_attribute.sub("", text)  # 删除属性


# %% ---------------------------------------------------------------------------
# 删除空行
# ------------------------------------------------------------------------------
# def clean_empty_line(text: str) -> str:
#     """
#     删除空行\n
#     text: str => 输入文本\n
#     return: str => 处理后的文本
#     """
#     return re_empty_line.sub("", text)  # 删除空行


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
