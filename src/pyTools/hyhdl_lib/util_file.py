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
import tempfile
from pathlib import Path

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
