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
const { promisify } = require("util")
const writeFileAsync = promisify(fs.writeFile)
const readFileAsync = promisify(fs.readFile)
const execAsync = promisify(require('child_process').exec)

//------------------------------------------------------------------------------
class formatter {
    constructor(context) {
        this.context = context;
    }

    // save the code in %tmp%, with "utf-8"
    async _save_code(document) {
        if (document === undefined) {
            return ""
        }
        // save the code to OS.tempFile, with "utf-8"
        const tmpFile = path.join(os.tmpdir(), 'code')
        await writeFileAsync(tmpFile, document.getText(), 'utf-8')
        return tmpFile
    }

    // get the path of the "pyTool"
    _get_pyTool() {
        let pyFmt = path.join(this.context.extensionUri.fsPath, "src", "pyTools", "verilogFormatter")
        pyFmt += (os.platform() == 'win32') ? ".exe" : ".py"
        return pyFmt
    }

    async doFormat(document) {
        // save the code in %tmp%, with "utf-8"
        const tmpFile = await this._save_code(document)
        if (!tmpFile) {
            return []
        }
        // format command
        let pyToolCmd = this._get_pyTool() + ` -i "${tmpFile}"`
        // run command
        const { stderr } = await execAsync(pyToolCmd)
        if (stderr) {
            console.log(stderr)
            return []
        }
        // return
        const fmtCode = await readFileAsync(tmpFile, "utf8")
        return [
            new vscode.TextEdit(new vscode.Range(document.lineAt(0).range.start, document.lineAt(document.lineCount - 1).range.end), fmtCode)
        ]
    }
}
//------------------------------------------------------------------------------
module.exports = {
    formatter
}
