// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
const vscode = require('vscode');

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    // instantiation
    let dispo_inst = vscode.commands.registerCommand('hyhdl.instantiation', () => {
        vscode.window.showInformationMessage('module 例化');
    });
    context.subscriptions.push(dispo_inst);
    // testbench
    let dispo_tb = vscode.commands.registerCommand('hyhdl.testbench', () => {
        vscode.window.showInformationMessage('生成 testbench');
    });
    context.subscriptions.push(dispo_tb);
    // documentation
    let dispo_doc = vscode.commands.registerCommand('hyhdl.documentation', () => {
        vscode.window.showInformationMessage('生成文档');
    });
    context.subscriptions.push(dispo_doc);
}

function deactivate() { }

module.exports = {
    activate,
    deactivate
}
