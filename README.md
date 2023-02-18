# 1. About this Extension
Generate the code of instantiation or testbench, the documentation of the module

## 1.1. Features
- Instantiation and Testbench generation
    - Verilog: ok
    - SystemVerilog: partially compatible
- Documentation
    - Verilog: ok
    - SystemVerilog: partially compatible

## 1.2. Usage
* Instantiation
    1. open a verilog file
    2. at the top right corner of the editor, there is a button named `hyhdl.instantiation`, click it
    3. the instantiation code will be copy into the clipboard, you can just copy it anywhere
* Testbench
    1. open a verilog file
    2. at the top right corner of the editor, there is a button named `hyhdl.testbench`, click it
    3. a new editor contains the testbench code will be opend
    </br>
    * user can specify the testbench template by changing the etxtension setting: `Testbench template file path`
* Documentation
    1. open a verilog file
    2. at the top right corner of the editor, there is a button named `hyhdl.documentation`, click it
    3. at the right column of the vscode, a preview of documentation will be shown
        * the module statement MUST follow the **ANSI** style, for example
            ``` verilog
            module Uart_Rx_x81
            #(  // parameters
                parameter CLK_FREQ        = 100000000, // 主时钟的频率
                parameter BAUDRATE        =    115200, // 波特率
                parameter BAUD_PRSCL_BITS =        10, // 波特率分频器的位数, = ceil( log2(CLK_FREQ/BAUDRATE) )
                parameter PARITY          =         0  // 校验模式: 0 = None; 1 = Odd; 2 = Even
            ) (
                //system signal
                input       clk,    // 主时钟
                // pins -> this
                input       RxdPin,                 // RXD pin
                // this -> received data
                output reg          rx_tvalid = 0,  // 接收数据的 tvalid
                output reg  [ 7: 0] rx_tdata        // 接收数据的 tdata
            );
            ```
        * the block diagram of the module will be shown
        * the tables of the parameters and ports of the module will be shown
        * the comment lines starting with `//>` will be shown (the block commemts will not be shown), for example:
            ```verilog
            //> Copyright(C): hid4net <hid4net@outlook.com>
            // Description:
            ```
            * the 1st line will be shown in the preview
            * the 2nd line will not be shown in the preview
        * the wavedorm data between `<wavedrom>` and `</wavedrom>` in the comments (starting with `//>`) will be shown in the preview, the key word `wavedrom` can be truncated to `wave`, for example
            ```verilog
            //>  <wave>
            //>     { signal: [
            //>         {name: 'Baud',  wave: 'P.......'},
            //>         {name: 'UART',  wave: '103=|451', data: ['LSB', '...', 'MSB', 'Par']},
            //>       ],
            //>     }
            //>  </wave>
            ```
        * the markdown table in the comments (starting with `//>`) will be shown in the preview, for example:
            ```verilog
            //>  Version | Author  | Date     | Changes
            //>  :-----: | :-----: | :------: | --------------------
            //>  0.1     | someone | some day | some features added
            //>  0.2     | someone | some day | some features added
            //>  0.3     | someone | some day | some features added
            ```
        * the preview will be refreshed when the verilog file is saved
    4. if a offline HTML file of the documentation needs to be saved, click the button `Export HTML` at the top right corner of the preview, the file will be save in the same directory as the verilog code

## 1.4. Extension Settings
* `Testbench template file path`: user specified testbench template
    * in which, the symbol `{{module_name}}` will be replaced with module name, and the symbol `{{uut}}` will be replaced with signals definition and module instantiation
    * the template file should be encoded with `utf-8`
    * if not used, make it empty

## 1.5. Known Issues, Bugs Feedback
* this extension is only tested with verilog files, and only tested in Windows 10
    * this extension is ought to work in linux or MAC OS with python 3.10 (with lib `PyYaml` and `Jinja2`) installed
    * this extension may not work regularly for SystemVerilog
* If a bug occurs, please e-mail the `hyhdl_dump` file to _hid4net@outlook.com_
    * the `hyhdl_dump` file is stored in the OS's temporary directory
        * for windows: the OS's temporary directory can be found by the command: `echo %tmp%`
* I'm an ordinary FPGA engineer, and my software skills and English sucks, don't fuck me please

## 1.6. Release Notes
* see [CHANGELOG.md](./CHANGELOG.md)

## 1.7. Thanks
* vscode extension: [mshr-h/vscode-verilog-hdl-support](https://github.com/mshr-h/vscode-verilog-hdl-support)
* vscode extension: [TerosTechnology/vscode-terosHDL](https://github.com/TerosTechnology/vscode-terosHDL)
* vscode extension: [Bestduan/Digital-IDE](https://github.com/Bestduan/Digital-IDE)

----------------------------------------------------------------
# 2. 设计思路 (Chinese)
- FPGA 工程师一般不会用到 javascript, 因此 js 代码要尽量少，能用 `python` 的尽量不用 js

## 2.1. 功能模块设计
- 例化代码的生成
    - 在 `TextEditor` 右上角添加命令按钮
    1. 从当前 `TextEditor` 提取代码, 保存到系统临时文件 (以 utf-8 格式存储, 防止乱码)
    2. 调用 `hyhdl.exe` (由 python 代码打包的程序) 程序处理代码, 并保存到系统临时文件 (以 utf-8 格式存储, 防止乱码)
    3. 插件从系统临时文件读取例化代码, 并写到系统剪切板
- testbench 代码的生成
    - 在 `TextEditor` 右上角添加命令按钮
    1. 从当前 `TextEditor` 提取代码, 保存到系统临时文件 (以 utf-8 格式存储, 防止乱码)
    2. 调用 `hyhdl.exe` (由 python 代码打包的程序) 程序处理代码, 并保存到系统临时文件 (以 utf-8 格式存储, 防止乱码)
    3. 插件从系统临时文件读取 testbench, 并复制到新的 `TextEditor`
- 根据注释生成文档
    - 在 `TextEditor` 右上角添加命令按钮
    - 打开 `webview` 显示注释生成的文档信息, 并支持导出 `.html` 文件 (参考并移植 `teroshdl` 的代码)
    - 设计概述:
        - 打开 webview
            1. 触发命令 (`vscode.commands.registerCommand`) -> ...  -> `vscode.window.createWebviewPanel` -> ...
            2. 调用 `hyhdl.exe` (由 python 代码打包的程序) 生成 html ->
            3. 更新 html 到 webview
        - 实时更新 webview
            1. 注册 `vscode.workspace.onDidOpenTextDocument`, `vscode.workspace.onDidSaveTextDocument`, `vscode.window.onDidChangeVisibleTextEditors` 等事件 -> ... ->
            2. 调用 `hyhdl.exe` (由 python 代码打包的程序) 生成 html ->
            3. 更新 html 到 webview
        - 导出 webview
            1. `webview` 中触发消息 -> ... -> vscode 中接收消息 `<panel 变量>.webview.onDidReceiveMessage` ->
            2. 调用 `hyhdl.exe` (由 python 代码打包的程序) 生成 html ->
            3. 保存到源代码的目录中

## 2.2. todo
- 完善文档