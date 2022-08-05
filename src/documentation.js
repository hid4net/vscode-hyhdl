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

class documentor {
    panel = undefined
    curDocument = undefined
    /**
     * @param {vscode.ExtensionContext} context
     */
    constructor(context) {
        this.context = context;
    }

    openPreview() {
        let actEditor = vscode.window.activeTextEditor
        if (!actEditor) {
            return
        }
        let actDoc = actEditor.document
        if (actDoc === undefined) {
            return
        }

        if (this.panel === undefined) {
            this.panel = vscode.window.createWebviewPanel(
                'Documentation',
                'Preview: documentation',
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true,
                    localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, "src", "pyTools", "wavedrom")]
                }
            );
            this.panel.onDidDispose(
                () => { this.panel = undefined; },
                undefined,
                this.context.subscriptions
            );
            this.panel.webview.onDidReceiveMessage(
                message => {
                    if (message.command == "export") {
                        if (message.text == "html") {
                            this.exportHtml(message.text)
                        }
                    }
                },
                undefined,
                this.context.subscriptions
            );
        }
        //---------- 更新 html ----------
        this.updatePreview(actDoc);
    }

    // save the code in %tmp%, with "utf-8"
    _save_code(document) {
        // get code
        let code = document.getText()
        // save the code to OS.tempFile, with "utf-8"
        let tmpFile = path.join(os.tmpdir(), 'code')
        fs.writeFileSync(tmpFile, code, 'utf-8')
        return tmpFile
    }

    // get the path of the "pyTool"
    _get_pyTool() {
        let pyTool = path.join(this.context.extensionUri.fsPath, "src", "pyTools", "hyhdl")
        pyTool += (os.platform() == 'win32') ? ".exe" : ".py"
        return pyTool
    }

    updatePreview(document) {
        this.curDocument = document
        // save the code in %tmp%, with "utf-8"
        let tmpFile = this._save_code(document)
        // format command
        let pyToolCmd = this._get_pyTool() + ` -p "${tmpFile}"`
        // run command
        cp.exec(pyToolCmd, (err, stdout, stderr) => {
            if (err) {
                console.log(err);
                console.log(stderr);
                return
            }
            //---------- update preview ----------
            tmpFile = stdout.replace("\r", "").replace("\n", "");
            this.panel.webview.html = fs.readFileSync(tmpFile, "utf8");
        });
    }

    exportHtml(export_type) {
        let docPath = this.curDocument.uri.fsPath
        if (fs.existsSync(docPath)) {   // 判断文件是否保存在硬盘中
            // save the code in %tmp%, with "utf-8"
            let tmpFile = this._save_code(this.curDocument)
            // format command
            let pyToolCmd = this._get_pyTool() + ` -h "${tmpFile}"`
            // run command
            cp.exec(pyToolCmd, (err, stdout, stderr) => {
                if (err) {
                    console.log(err);
                    console.log(stderr);
                    return
                }
                tmpFile = stdout.replace("\r", "").replace("\n", "");
                // export the html
                let tPath = path.parse(docPath)
                let html_path = path.join(tPath.dir, tPath.name + ".html")
                fs.copyFileSync(tmpFile, html_path)
                vscode.window.showInformationMessage(`hyhdl: The README document has been exported to ${html_path}`)
            });
        }
        else {
            vscode.window.showWarningMessage(`hyhdl: currently edited file needs be saved firstly`)
        }
    }

    updateOpenedPreview(document) {
        let langId = document.languageId
        if (langId !== "verilog" && langId !== "systemverilog") {
            return
        }
        this.updatePreview(document)
    }

    updatePreviewOnVisible(textEditors) {
        if (textEditors.length === 0) {
            return
        }
        let document = textEditors[textEditors.length - 1].document
        this.updateOpenedPreview(document)
    }
}
//------------------------------------------------------------------------------
module.exports = {
    documentor
}
