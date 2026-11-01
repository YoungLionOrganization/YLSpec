// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const vscode = require('vscode');
const {template, fields} = require('../src/metadata.cjs');
exports.run = async () => {
  const {publisher, name} = require('../package.json');
  const extension = vscode.extensions.getExtension(`${publisher}.${name}`);
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
  const isMetadataCompletion = item => item.label === 'profile_version' &&
    item.kind === vscode.CompletionItemKind.Property && item.detail === fields.profile_version.detail;
  assert.ok(completion.items.some(isMetadataCompletion));
  async function accept(source, label, trigger) {
    const offset = source.indexOf('|');
    const document = await vscode.workspace.openTextDocument({language: 'ylspec', content: source.replace('|', '')});
    const position = document.positionAt(offset);
    const result = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', document.uri, position, trigger);
    const item = result.items.find(item => item.label === label);
    assert.ok(item, `Missing completion ${label}`);
    const range = item.range?.replacing || item.range;
    assert.ok(range, 'Completion must explicitly replace its partial token');
    const edit = new vscode.WorkspaceEdit();
    assert.equal(typeof item.insertText, 'string');
    edit.replace(document.uri, range, item.insertText);
    assert.ok(await vscode.workspace.applyEdit(edit));
    return document;
  }
  const headerDocument = await accept('[|]', '_ylspec', '[');
  assert.equal(headerDocument.getText(), '[_ylspec]');
  const booleanDocument = await accept(template + 'enabled=t|rue # retained\n', 'true');
  assert.equal(booleanDocument.getText(), template + 'enabled=true # retained\n');
  await api.validate(booleanDocument);
  assert.equal(vscode.languages.getDiagnostics(booleanDocument.uri).length, 0);
  const valueDocument = await accept('[_ylspec]\nprofile="co|re.data"', '"core.data"', '"');
  assert.equal(valueDocument.getText(), '[_ylspec]\nprofile="core.data"');
  const arrayDocument = await vscode.workspace.openTextDocument({language: 'ylspec', content: template + 'flags=[]\n'});
  const arrayPosition = arrayDocument.positionAt(arrayDocument.getText().indexOf('[]') + 1);
  const arrayItems = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', arrayDocument.uri, arrayPosition, '[');
  assert.ok(arrayItems.items.some(item => item.label === 'false'));
  const completionSettings = vscode.workspace.getConfiguration('ylspec', completionDocument.uri);
  async function setCompletionEnabled(value) {
    let subscription;
    const applied = new Promise(resolve => {
      subscription = vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration('ylspec.completion.enabled', completionDocument.uri)) resolve();
      });
    });
    try {
      await completionSettings.update('completion.enabled', value, vscode.ConfigurationTarget.Global);
      await applied;
    } finally {subscription.dispose();}
  }
  await setCompletionEnabled(false);
  try {
    assert.equal(vscode.workspace.getConfiguration('ylspec', completionDocument.uri).get('completion.enabled'), false);
    const disabled = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', completionDocument.uri, new vscode.Position(1, 3));
    // Other VS Code providers may still offer words seen in open documents.
    assert.ok(!disabled.items.some(isMetadataCompletion), JSON.stringify(disabled.items.map(item => ({label: item.label, kind: item.kind, detail: item.detail}))));
  } finally {await setCompletionEnabled(undefined);}
  const settings = vscode.workspace.getConfiguration('ylspec', document.uri);
  await settings.update('format.enabled', true, vscode.ConfigurationTarget.Global);
  try {
    const formatted = await vscode.commands.executeCommand('vscode.executeFormatDocumentProvider', document.uri, {tabSize: 2, insertSpaces: true});
    assert.ok(formatted.length > 0, 'Formatter must provide edits');
    const edits = new vscode.WorkspaceEdit(); edits.set(document.uri, formatted);
    assert.ok(await vscode.workspace.applyEdit(edits));
    const {createClient} = await import(pathToFileURL(path.resolve(__dirname, '../engine/src/web.mjs')).href);
    const yl = await createClient({wasmBinary: readFileSync(path.resolve(__dirname, '../engine/wasm/core.wasm'))});
    assert.deepEqual(yl.loads(document.getText()).root, yl.loads(template).root);
    await api.validate(document); assert.equal(vscode.languages.getDiagnostics(document.uri).length, 0);
  } finally {await settings.update('format.enabled', undefined, vscode.ConfigurationTarget.Global);}
  console.log('YLSpec VS Code extension integration tests passed');
};
