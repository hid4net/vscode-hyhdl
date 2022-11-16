//==============================================================================
//DESCRIPTION:
// *
//
//MODIFICATION HISTORY:---------------------------------------------------------
//   Version | Author | Date       | Changes
//   :-----: | :----: | :--------: | -------------------------------------------
//   0.1     | hid4net | 2022-05-12 | start to coding
//
//==============================================================================
"use strict"
//------------------------------------------------------------------------------
const vscode = require('vscode')
const os = require("os")
const path = require('path')
const fs = require('fs')
const cp = require('child_process')

//------------------------------------------------------------------------------

class vlgInstTb {
    constructor(context) {
        this.context = context;
    }

    // save the code in %tmp%, with "utf-8"
    _save_code() {
        // get code
        const actEditor = vscode.window.activeTextEditor
        if (!actEditor) {
            return ""
        }
        const code = actEditor.document.getText()
        // save the code to OS.tempFile, with "utf-8"
        const tmpFile = path.join(os.tmpdir(), 'code')
        fs.writeFileSync(tmpFile, code, 'utf-8')
        return tmpFile
    }

    // get the path of the "pyTool"
    _get_pyTool() {
        let pyTool = path.join(this.context.extensionUri.fsPath, "src", "pyTools", "hyhdl")
        if (os.platform() == 'win32') {
            pyTool += '.exe'
        } else {
            pyTool = "python3 " + pyTool + '.py'
        }
        return pyTool
    }

    get_inst() {
        // save the code in %tmp%, with "utf-8"
        let tmpFile = this._save_code()
        if (!tmpFile) {
            return
        }
        // format command
        let pyToolCmd = this._get_pyTool() + ` -i "${tmpFile}"`
        // run command
        cp.exec(pyToolCmd, (err, stdout, stderr) => {
            if (err) {
                console.log(err);
                console.log(stderr);
                return
            }
            tmpFile = stdout.replace("\r", "").replace("\n", "");
            // write the code of instantiation to the clipboard
            vscode.env.clipboard.writeText(fs.readFileSync(tmpFile, "utf8"))
            vscode.window.showInformationMessage(`hyhdl: the instantiation code is copied to the clipboard`)
        });
    }

    // get the testbench template file
    _get_tb_template() {
        let templateFile = vscode.workspace.getConfiguration("hyhdl").get("Testbench template file path")
        if (templateFile !== "") {
            if (!fs.existsSync(templateFile)) {
                vscode.window.showWarningMessage(`user specified testbench template does not exist, using default template`)
                templateFile = ""
            }
        }
        return templateFile
    }

    get_testbench() {
        // save the code in %tmp%, with "utf-8"
        let tmpFile = this._save_code()
        if (!tmpFile) {
            return
        }
        // get the testbench template file
        const templateFile = this._get_tb_template()
        // format command
        let pyToolCmd = this._get_pyTool() + ` -t "${tmpFile}"`
        if (templateFile) {
            pyToolCmd += ` -T "${templateFile}"`
        }
        // run command
        cp.exec(pyToolCmd, (err, stdout, stderr) => {
            if (err) {
                console.log(err);
                console.log(stderr);
                return
            }
            tmpFile = stdout.replace("\r", "").replace("\n", "");
            // copy the testbench to an new document
            const newDoc = vscode.workspace.openTextDocument({ language: "verilog", content: fs.readFileSync(tmpFile, "utf8") })
            vscode.window.showTextDocument(newDoc)
            vscode.window.showInformationMessage(`hyhdl: The code of testbench has been generated`)
        });
    }
}
//------------------------------------------------------------------------------
module.exports = {
    vlgInstTb
}
