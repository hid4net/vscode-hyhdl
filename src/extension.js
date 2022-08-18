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
//==============================================================================
const vscode = require('vscode');
const codeTemplate = require('./codeTemplate')      // myCode: realize instantiation and testbench generation
const documentation = require('./documentation')    // myCode: realize documentation
const formatter = require('./formatter')            // myCode: realize formatter
//------------------------------------------------------------------------------
/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    //---------- codeTemplate: instantiation and testbench ----------
    const vlgInstTb = new codeTemplate.vlgInstTb(context) // myCode: instantiate a object
    context.subscriptions.push(vscode.commands.registerCommand('hyhdl.instantiation', () => { vlgInstTb.get_inst() }));     // myCode: enable the command of instantiation
    context.subscriptions.push(vscode.commands.registerCommand('hyhdl.testbench', () => { vlgInstTb.get_testbench() }));    // myCode: enable the command of testbench
    //---------- documentation ----------
    const myDocumentor = new documentation.documentor(context) // myCode: instantiate a object
    context.subscriptions.push(
        vscode.commands.registerCommand('hyhdl.documentation', () => { myDocumentor.openPreview() }),   // myCode: enable the command of documentation
        vscode.workspace.onDidOpenTextDocument((e) => { myDocumentor.updateOpenedPreview(e) }),         // myCode: update the documentation preview when an new verilog file is open
        vscode.workspace.onDidSaveTextDocument((e) => { myDocumentor.updateOpenedPreview(e) }),         // myCode: update the documentation preview when the current verilog file is saved
        // vscode.window.onDidChangeActiveTextEditor((e) => (myDocumentor.updateOpenedPreview(e))),
        vscode.window.onDidChangeVisibleTextEditors((e) => { myDocumentor.updatePreviewOnVisible(e) }), // myCode: update the documentation preview when the visibility of the verilog file is changed
    );
    //---------- formatter ----------
    const enFmt = vscode.workspace.getConfiguration("hyhdl").get("Enable formatter")    // myCode: instantiate a object
    if (enFmt) {
        const myFormatter = new formatter.formatter(context)
        context.subscriptions.push(
            vscode.languages.registerDocumentFormattingEditProvider(    // myCode: register formatter
                [{ scheme: "file", language: "verilog" }, { scheme: "file", language: "systemverilog" }],   // myCode: avaliable file type
                { provideDocumentFormattingEdits(document) { return myFormatter.doFormat(document) } }      // myCode: do format
            )
        );
    }
}
//------------------------------------------------------------------------------
function deactivate() { }
//------------------------------------------------------------------------------
module.exports = {
    activate,
    deactivate
}
