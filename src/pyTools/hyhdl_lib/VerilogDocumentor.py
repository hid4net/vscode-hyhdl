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
from pathlib import Path
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader

from .util_file import write_to_tmpfile
from .VerilogParser import VerilogParser


# %% ---------------------------------------------------------------------------
# class: Documentor
# ------------------------------------------------------------------------------
class VerilogDocumentor(VerilogParser):
    """
    处理 verilog 文件
    """

    # ------------------------------------------------------------------------------
    # 初始化 Documentor, 读取文件并提取需要出来的代码
    # ------------------------------------------------------------------------------
    def __init__(self, file: str, pytools_dir: str) -> None:
        """
        初始化 Documentor, 读取文件并提取需要出来的代码\n
        pytools_dir:str => pyTools 的路径
        file: str => verilog 文件路径
        """
        # -------- init --------
        super().__init__(file)
        self.parse_module()
        self.parse_comment()
        self.__pytools_dir = pytools_dir

    # ------------------------------------------------------------------------------
    # draw the block diagram
    # ------------------------------------------------------------------------------
    def _draw_module_bd(self) -> None:
        """
        绘制 module 的框图
        """
        # -------- 如果没有端口, 不画图 --------
        if self.module_ports == []:
            return ""
        # -------- 整理数据 --------
        parameters = self.module_parameters
        ports_left = [x for x in self.module_ports if x["direction"] == "input"]
        ports_right = [x for x in self.module_ports if x["direction"] in ("output", "inout")]
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

    # ------------------------------------------------------------------------------
    # 格式化注释 -> html
    # ------------------------------------------------------------------------------
    def _get_notes_html(self) -> str:
        """
        格式化注释, 生成 html\n
        return: str => 由注释转换而来的 html 字符串
        """
        # -------- 如果没有需要处理的 comment_items --------
        if self.comment_items == []:
            return ""
        comment_items = self.comment_items
        notes_html = ""
        # -------- 处理 comment_items --------
        for item in comment_items:
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

    # ------------------------------------------------------------------------------
    # 生成预览用的 html
    # ------------------------------------------------------------------------------
    def get_preview_html(self, template_fname: str) -> str:
        """
        生成预览用的 html
        template_fname: str => testbench template file
        return: str => html 的路径
        """
        # -------- 初始化变量 --------
        tmplt_path = Path(template_fname)
        if not tmplt_path.exists():
            return ""
        # -------- 整理数据 --------
        # VS_EXT_PATH_PREFIX = "vscode-resource:/"
        # pytools_dir = Path(self.__pytools_dir)
        # wavedrom_js_path = VS_EXT_PATH_PREFIX + quote(  # 需要使用 vscode 的安全协议
        #     pytools_dir.joinpath("wavedrom", "wavedrom.min.js").as_posix()
        # )
        # wavedrom_theme_path = VS_EXT_PATH_PREFIX + quote(  # 需要使用 vscode 的安全协议
        #     pytools_dir.joinpath("wavedrom", "default.js").as_posix()
        # )
        parameters = self.module_parameters
        ports = self.module_ports
        hasWavedrom = self.has_wavedrom
        if hasWavedrom:
            pytools_dir = Path(self.__pytools_dir)
            with Path(pytools_dir).joinpath("wavedrom", "wavedrom.min.js").open("r",encoding="utf-8") as fp:
                wavedrom_js_text = fp.read()
            with Path(pytools_dir).joinpath("wavedrom", "default.js").open("r",encoding="utf-8") as fp:
                wavedrom_theme_text = fp.read()
        else:
            wavedrom_js_text = ""
            wavedrom_theme_text = ""
        # -------- 替换模板 --------
        env = Environment(loader=FileSystemLoader(tmplt_path.parent))
        tmpl = env.get_template(tmplt_path.name)
        text = tmpl.render(
            hasWavedrom=hasWavedrom,
            # wavedrom_js_path=wavedrom_js_path,
            # wavedrom_theme_path=wavedrom_theme_path,
            wavedrom_js_text=wavedrom_js_text,
            wavedrom_theme_text=wavedrom_theme_text,
            module_name=self.module_name,
            module_diagram=self._draw_module_bd(),
            parameters=parameters,
            hasParameters=len(parameters) > 0,
            ports=ports,
            hasPorts=len(ports) > 0,
            notes_html=self._get_notes_html(),
        )
        # -------- 写入临时文件 --------
        return write_to_tmpfile("hyhdl_output", text)

    # ------------------------------------------------------------------------------
    # 生成导出用的 html
    # ------------------------------------------------------------------------------
    def get_export_html(self, template_fname: str) -> str:
        """
        生成导出用的 html\n
        return: str => html 的路径
        """
        # -------- 初始化变量 --------
        tmplt_path = Path(template_fname)
        if not tmplt_path.exists():
            return ""
        # -------- 整理数据 --------
        parameters = self.module_parameters
        ports = self.module_ports
        hasWavedrom = self.has_wavedrom
        if hasWavedrom:
            pytools_dir = Path(self.__pytools_dir)
            with Path(pytools_dir).joinpath("wavedrom", "wavedrom.min.js").open("r",encoding="utf-8") as fp:
                wavedrom_js_text = fp.read()
            with Path(pytools_dir).joinpath("wavedrom", "default.js").open("r",encoding="utf-8") as fp:
                wavedrom_theme_text = fp.read()
        else:
            wavedrom_js_text = ""
            wavedrom_theme_text = ""

        # -------- 替换模板 --------
        env = Environment(loader=FileSystemLoader(tmplt_path.parent))
        tmpl = env.get_template(tmplt_path.name)
        text = tmpl.render(
            hasWavedrom=hasWavedrom,
            wavedrom_js_text=wavedrom_js_text,
            wavedrom_theme_text=wavedrom_theme_text,
            module_name=self.module_name,
            module_diagram=self._draw_module_bd(),
            parameters=parameters,
            hasParameters=len(parameters) > 0,
            ports=ports,
            hasPorts=len(ports) > 0,
            notes_html=self._get_notes_html(),
        )
        # -------- 写入临时文件 --------
        return write_to_tmpfile("hyhdl_output", text)
