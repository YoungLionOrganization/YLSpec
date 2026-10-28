// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const assert = require('node:assert/strict');
const vscode = require('vscode');
const {template} = require('../src/metadata.cjs');
exports.run = async () => {
  const extension = vscode.extensions.getExtension('YoungLionOrganization.ylspec');
  assert.ok(extension, 'Extension must be installed in the development host');
  const api = await extension.activate();
  const document = await vscode.workspace.openTextDocument({language: 'ylspec', content: template});
  await vscode.window.showTextDocument(document);
  await api.validate(document);
  assert.equal(vscode.languages.getDiagnostics(document.uri).length, 0);
  const broken = await vscode.workspace.openTextDocument({language: 'ylspec', content: template + 'broken = [\n'});
  await api.validate(broken);
  const diagnostics = vscode.languages.getDiagnostics(broken.uri);
  assert.equal(diagnostics.length, 1); assert.equal(diagnostics[0].severity, vscode.DiagnosticSeverity.Error);
  assert.equal(diagnostics[0].source, 'YLSpec');
  const unknown = await vscode.workspace.openTextDocument({language: 'ylspec', content: template.replace('core.data', 'example.custom')});
  await api.validate(unknown); assert.equal(vscode.languages.getDiagnostics(unknown.uri)[0].severity, vscode.DiagnosticSeverity.Warning);
  const completionDocument = await vscode.workspace.openTextDocument({language: 'ylspec', content: '[_ylspec]\npro'});
  const completion = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', completionDocument.uri, new vscode.Position(1, 3));
  assert.ok(completion.items.some(item => item.label === 'profile_version'));
  const settings = vscode.workspace.getConfiguration('ylspec', document.uri);
  await settings.update('format.enabled', true, vscode.ConfigurationTarget.Global);
  try {
    const formatted = await vscode.commands.executeCommand('vscode.executeFormatDocumentProvider', document.uri, {tabSize: 2, insertSpaces: true});
    assert.ok(formatted.length > 0, 'Formatter must provide edits');
    const edits = new vscode.WorkspaceEdit(); edits.set(document.uri, formatted);
    assert.ok(await vscode.workspace.applyEdit(edits));
    assert.match(document.getText(), /\[data\]/);
    await api.validate(document); assert.equal(vscode.languages.getDiagnostics(document.uri).length, 0);
  } finally {await settings.update('format.enabled', undefined, vscode.ConfigurationTarget.Global);}
  console.log('YLSpec VS Code extension integration tests passed');
};
