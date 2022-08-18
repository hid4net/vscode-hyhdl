# ==============================================================================
# AUTHOR: hid4net<hid4net@outlook.com>
# DESCRIPTION:
# * 使用
# *     usage: hyhdl.exe [-h] (-i | -t | -p | -e) [-T T] [verilog_file]
# *
# *     Generate the instantiation, testbench and documentation for verilog
# *
# *     positional arguments:
# *       verilog_file  file path of verilog file
# *
# *     options:
# *       -h, --help    show this help message and exit
# *       -i            generate instantiation
# *       -t            generate testbench
# *       -p            generate documentation html for vscode preview
# *       -e            generate documentation html for export
# *       -T T          file path of template file (only used for testbench)
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
import argparse
# from line_profiler import *
import sys
import tempfile
from pathlib import Path

from hyhdl_lib import VerilogInstTb, VerilogDocumentor

# %% ---------------------------------------------------------------------------
# global variable
# ------------------------------------------------------------------------------
pyTool_dir = ""
# %% ---------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------
# @profile
def main(option, verilog_file, template_file):
    if option == 1:  # for instantiation
        pyTool = VerilogInstTb(verilog_file)
        tmpf = pyTool.get_inst()
        # ! debug start
        pyTool.dump_parsed()
        # ! debug end
    elif option == 2:  # for testbench
        pyTool = VerilogInstTb(verilog_file)
        tmpf = pyTool.get_testbench(template_file)
        # ! debug start
        pyTool.dump_parsed()
        # ! debug end
    elif option == 3:  # for preview
        pyTool = VerilogDocumentor(verilog_file, pyTool_dir)
        tmpf = pyTool.get_preview_html(pyTool_dir.joinpath("previewTemplate.html"))
        # ! debug start
        pyTool.dump_parsed(dump_comment=True)
        # ! debug end
    elif option == 4:  # for export html
        pyTool = VerilogDocumentor(verilog_file, pyTool_dir)
        tmpf = pyTool.get_export_html(pyTool_dir.joinpath("exportTemplate.html"))
        # ! debug start
        pyTool.dump_parsed(dump_comment=True)
        # ! debug end

    print(tmpf, end=None)


# %%
if __name__ == "__main__":
    pyTool_dir = Path(sys.argv[0]).absolute().parent

    ap = argparse.ArgumentParser(
        description="Generate the instantiation, testbench and documentation for verilog"
    )

    apg = ap.add_mutually_exclusive_group(required=True)
    apg.add_argument(
        "-i",
        action="store_const",
        const=1,
        dest="opt",
        help="generate instantiation",
    )
    apg.add_argument(
        "-t",
        action="store_const",
        const=2,
        dest="opt",
        help="generate testbench",
    )
    apg.add_argument(
        "-p",
        action="store_const",
        const=3,
        dest="opt",
        help="generate documentation html for vscode preview",
    )
    apg.add_argument(
        "-e",
        action="store_const",
        const=4,
        dest="opt",
        help="generate documentation html for export",
    )

    ap.add_argument(
        "verilog_file",
        nargs="?",
        # type=argparse.FileType("r", encoding="utf-8"),
        default=Path(tempfile.gettempdir()).joinpath("code"),
        help="file path of verilog file",
    )

    ap.add_argument(
        "-T",
        action="store",
        # type=argparse.FileType("r", encoding="utf-8"),
        help="file path of template file (only used for testbench)",
    )

    arg_parsed = ap.parse_args()

    opt = arg_parsed.opt
    verilog_file = arg_parsed.verilog_file
    template_file = arg_parsed.T

    # print(f"{opt=}")
    # print(f"{verilog_file=}")
    # print(f"{template_file=}")

    main(opt, verilog_file, template_file)
