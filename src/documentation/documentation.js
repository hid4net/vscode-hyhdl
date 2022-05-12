//==============================================================================
//DESCRIPTION:
// *
//
//MODIFICATION HISTORY:---------------------------------------------------------
//   Version | Author | Date       | Changes
//   :-----: | :----: | :--------: | -------------------------------------------
//   0.1     | WangXH | 2022-05-12 | start to coding
//
//==============================================================================
"use strict"
//------------------------------------------------------------------------------
const vscode = require('vscode');
const path_lib = require('path');
//------------------------------------------------------------------------------

class documentor {
    panel = undefined
    curDocument = undefined
    curDocumentPath = undefined
    //
    cats = {
        'Coding Cat': 'https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif',
        'Compiling Cat': 'https://media.giphy.com/media/mlvseq9yvZhba/giphy.gif'
    };
    // -> param {vscode.ExtensionContext} context
    constructor(context) {
        this.context = context;
    }

    getActiveDocument() {
        let actEditor = vscode.window.activeTextEditor
        if (!actEditor) {
            return undefined
        }
        return actEditor.document
    }

    openPreview() {
        let activeDocument = this.getActiveDocument()
        if (activeDocument === undefined) {
            return
        }
        // this.curDocumentPath = activeDocument.uri.fsPath

        if (this.panel === undefined) {
            this.panel = vscode.window.createWebviewPanel(
                'Documentation',
                'Preview: documentation',
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );
            this.panel.onDidDispose(
                () => { this.panel = undefined; },
                null,
                this.context.subscriptions
            );
            this.panel.webview.onDidReceiveMessage(
                message => {
                    if (message.command == "export") {
                        vscode.window.showInformationMessage('需要实现的功能: 导出 Preview');
                        return;
                    }
                },
                undefined,
                this.context.subscriptions
            );
        }
        //---------- 更新 html ----------
        this.updatePreview(activeDocument);
    }

    // async updatePreview(document) {
    updatePreview(document) {
        let code = document.getText()
        // console.log(code)
        // todo ---------- 将 code(:string) 传入 python 程序, 生成 html (:string) ----------

        vscode.window.showWarningMessage('需要实现的功能: 更新 Preview');

        const html = `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cat Coding</title>
        </head>
        <body>
            <img src="https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif" width="300" />
        </body>
        </html>`

        //---------- 显示 preview ----------
        this.panel.webview.html = html;
    }
}
//------------------------------------------------------------------------------
module.exports = {
    documentor
}
