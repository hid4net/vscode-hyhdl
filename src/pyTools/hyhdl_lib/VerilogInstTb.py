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
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .VerilogParser import VerilogParser
from .util_file import write_to_tmpfile

# %% ---------------------------------------------------------------------------
# const
# ------------------------------------------------------------------------------

# %% ---------------------------------------------------------------------------
# global variables
# ------------------------------------------------------------------------------

# %% ---------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
class VerilogInstTb(VerilogParser):
    """
    处理 verilog 文件
    """

    # ------------------------------------------------------------------------------
    # 初始化 InstTb, 读取文件并提取需要出来的代码
    # ------------------------------------------------------------------------------
    def __init__(self, file: str) -> None:
        """
        初始化 InstTb, 读取文件并提取需要出来的代码\n
        file: str => verilog 文件路径
        """
        # -------- init --------
        super().__init__(file)
        self.parse_module()

    # ------------------------------------------------------------------------------
    # 生成例化代码
    # ------------------------------------------------------------------------------
    def get_inst(self) -> str:
        """
        生成端口例化代码\n
        return: str => 端口例化代码
        """
        # -------- 整理数据 --------
        module_name = self.module_name
        parameters = self.module_parameters
        ports = self.module_ports

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

    # ------------------------------------------------------------------------------
    # 生成 testbench
    # ------------------------------------------------------------------------------
    def get_testbench(self, template_fname: str) -> str:
        """
        生成端口例化代码\n
        template_fname: str => testbench template file\n
        return: str => 端口例化代码
        """
        # -------- 整理数据 --------
        module_name = self.module_name
        parameters = self.module_parameters
        ports = self.module_ports
        if not (module_name and ports):
            return ""

        tPath = Path(template_fname)
        # -------- 生成 uut 代码 --------
        uut = ""
        # uut += f"    // module instantiation\n"
        # 输出 parameters 的声明
        if len(parameters):
            param_names = [x["name"] for x in parameters]
            values = [x["value"] for x in parameters]
            name_width = ((max(map(len, param_names)) + 2) // 4) * 4 + 2
            # value_width = ((max(map(len, values)) + 2) // 4) * 4 + 2
            value_width = max(map(len, values))

            uut += f"    // parameters\n"
            for p in parameters:
                uut += (
                    f'    parameter {p["name"].ljust(name_width)}= {p["value"].ljust(value_width)};'
                    f'  // {p["description"]}\n'
                )
        # 输出 ports 的声明
        port_names = [x["name"] for x in ports]
        # name_width = (max(map(len, port_names)) // 4) * 4 + 4
        name_width = max(map(len, port_names))

        def get_port_rng(port_type):
            if r_m := re.search(r"\[.+:.+\]", port_type, re.S):
                rng = re.sub(r"\s+", " ", r_m.group(0))
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
                f'  // {p["description"]}\n'
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
        env = Environment(loader=FileSystemLoader(tPath.parent))
        tmpl = env.get_template(tPath.name)
        text = tmpl.render(
            module_name=module_name,
            uut=uut,
        )
        # -------- return --------
        return write_to_tmpfile("hyhdl_output", text)
