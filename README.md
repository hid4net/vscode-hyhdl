vscode-hyhdl

# 1. About this Extension
FPGA工程师写 bug 的小工具

> 正在开发, 还不能用

## 1.1. Features
- 语法高亮和配置 (Syntaxes Highlight / config)
    - [x] Verilog
    - [ ] SystemVerilog
    - [ ] VHDL
    - [ ] TCL
    - [ ] Xilinx xdc
- 语言服务协议的客户端 (Language Server Protocol (LSP) - client)
    - [ ] 语法错误诊断 (Publish Diagnostics, linting)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 自动补全 (Auto Completion)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 悬浮提示 (Hover)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 函数变量的提示 (Signature Help)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 转到定义 (Definition)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 转到引用 (References)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 文档符号 (Document Symbol)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 格式化 (Formatting)
        - [ ] Verilog: istyle, s3sv
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 选定范围的格式化 (RangeFormatting)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
    - [ ] 输入时格式化 (OnTypeFormatting)
        - [ ] Verilog
        - [ ] SystemVerilog
        - [ ] VHDL
        - [ ] TCL
- 例化和测试代码的生成 (Instantiation and Testbench generation)
    - [ ] Verilog
    - [ ] SystemVerilog
    - [ ] TCL
    - [ ] VHDL
- 根据注释生成文档 (Documentation)
    - [ ] Verilog
    - [ ] SystemVerilog
    - [ ] TCL
    - [ ] VHDL

## 1.2. Requirements
* 暂无

## 1.3. Extension Settings
* 暂无

## 1.4. Known Issues
* 暂无

## 1.5. Release Notes
* 暂无

----------------------------------------------------------------
# 2. 设计思路

## 2.1. 摘要
- 插件定位于 coding 的辅助, 尽量仅针对正在编辑的 HDL 文件及其直接引用的文件, 不考虑其所在的工程
- FPGA/ASIC 工程师一般不会用到 javascript, javascript 代码要尽量少; 为了便于共同维护, 使用 python 编程
- 语言的高级功能尽量使用已有的 LSP 服务器, 降低插件开发的难度

## 2.2. 各模块设计要点
- 语法高亮和配置
    - VS Code 的语法高亮基于 [TextMate](https://macromates.com/manual/en/language_grammars)
    - 使用 `yaml` 文件编辑和维护 `tmLanguage`, 然后转格式到 `json`
        > `yaml` 可读性好, 结构简单, 可以加注释
    - 语言配置文件尽量参考其它插件
- LSP 客户端
    - 尽量使用已有的 LSP 服务器
    - 语法错误诊断除了使用 LSP 服务器外, 还需支持 verilator, icarus, modelsim, xvlog
    - 自动补全, 定义, 符号等功能不仅需要考虑当前文件, 还需要考虑直接关联的文件, 如 verilog HDL 代码中 ``` `include <文件>```
    - 格式化工具尽量使用 LSP 服务器提供的, 如果没有, 使用外部的格式化工具, 如 iStyle, verilator, s3sc 等
- 例化和测试代码的生成
    - 研究能否基于 LSP 实现
    - 生成的代码放到剪切板或新文件
    - testbench: 从模板文件中导入例化端口前后的部分, 模板文件要允许用户自己提供
    - 在编辑器右上角添加命令按钮
- 根据注释生成文档
    - 参考并移植 `teroshdl` 的代码, 生成 `.md` 文件或 `.html` 文件
    - 在编辑器右上角添加命令按钮

## 2.3. 开发路线图
1. 本人最熟悉 verilog, 先从 verilog 入手开发, 开发顺序
    - [x] 语法高亮和配置
    - [ ] 根据注释生成文档
    - [ ] 研究 Verilog LSP-Server
    - [ ] 设计 Verilog LSP-client
        - [ ] 语法错误诊断 (Publish Diagnostics, linting)
        - [ ] 自动补全 (Auto Completion)
        - [ ] 悬浮提示 (Hover)
        - [ ] 函数变量的提示 (Signature Help)
        - [ ] 转到定义 (Definition)
        - [ ] 转到引用 (References)
        - [ ] 文档符号 (Document Symbol)
        - [ ] 格式化 (Formatting)
        - [ ] 选定范围的格式化 (RangeFormatting)
        - [ ] 输入时格式化 (OnTypeFormatting)
    - [ ] 例化和测试代码的生成
1. 实现 verilog 全部功能后, 发行第一版, 希望能有更多人支持
1. 如果有时间, 继续开发其它语言的支持
