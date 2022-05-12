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
//==============================================================================
const vscode = require('vscode');
const documentation = require('./documentation/documentation')
const codeTemplate = require('./codeTemplate/codeTemplate')
//------------------------------------------------------------------------------
/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    //---------- codeTemplate: instantiation ----------
    context.subscriptions.push(
        vscode.commands.registerCommand('hyhdl.instantiation',
            () => {
                vscode.window.showInformationMessage('module 例化');
            }
        )
    );
    //---------- codeTemplate: testbench ----------
    context.subscriptions.push(
        vscode.commands.registerCommand('hyhdl.testbench',
            () => {
                vscode.window.showInformationMessage('生成 testbench');
            }
        )
    );
    //---------- documentation ----------
    let myDocumentor = new documentation.documentor(context)
    context.subscriptions.push(
        vscode.commands.registerCommand('hyhdl.documentation', () => { myDocumentor.openPreview() })
    );

}
//------------------------------------------------------------------------------
function deactivate() { }
//------------------------------------------------------------------------------
module.exports = {
    activate,
    deactivate
}
