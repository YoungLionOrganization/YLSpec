// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
'use strict';
const vscode = require('vscode');
const {Worker} = require('node:worker_threads');
const path = require('node:path');
const {fields, template, tableAt, errorPosition} = require('./metadata.cjs');

function activate(context) {
  const diagnostics = vscode.languages.createDiagnosticCollection('ylspec');
  const timers = new Map(), pending = new Map();
  let worker, sequence = 0, disposed = false;
  function startWorker() {
    if (worker) return worker;
    const instance = new Worker(path.join(__dirname, 'worker.cjs'));
    worker = instance;
    instance.on('message', result => {const complete = pending.get(result.id); if (complete) {pending.delete(result.id); complete(result);}});
    const fail = message => {
      if (worker === instance) worker = undefined;
      for (const complete of pending.values()) complete({issue: {code: 'internal', message, warning: false}});
      pending.clear();
    };
    instance.on('error', error => fail('Cannot start the bundled YLSpec engine: ' + error.message));
    instance.on('exit', code => {if (!disposed && worker === instance) fail('YLSpec validation worker stopped with code ' + code);});
    return instance;
  }
  function config(document) {return vscode.workspace.getConfiguration('ylspec', document.uri);}
  async function inspect(document, format = false) {
    const settings = config(document), text = document.getText();
    const limits = {maxDocumentBytes: settings.get('maxDocumentBytes', 16777216), maxDepth: settings.get('maxDepth', 64)};
    if (Buffer.byteLength(text, 'utf8') > limits.maxDocumentBytes) return {issue: {message: 'Document exceeds the configured UTF-8 byte limit', code: 'limit'}};
    const id = ++sequence;
    return new Promise(resolve => {pending.set(id, resolve); startWorker().postMessage({id, text, limits, format});});
  }
  async function validate(document, explicit = false) {
    if (document.languageId !== 'ylspec' || document.isClosed) return;
    if (!explicit && !config(document).get('validation.enabled', true)) {diagnostics.delete(document.uri); return;}
    const version = document.version, result = await inspect(document);
    if (disposed || document.isClosed || document.version !== version) return;
    const issues = [];
    if (result.issue) {
      const issue = result.issue, position = errorPosition(document.getText(), issue);
      const start = new vscode.Position(position.line, position.character);
      const end = new vscode.Position(position.line, Math.min(document.lineAt(position.line).text.length, position.character + 1));
      const diagnostic = new vscode.Diagnostic(new vscode.Range(start, end), issue.message, issue.warning ? vscode.DiagnosticSeverity.Warning : vscode.DiagnosticSeverity.Error);
      diagnostic.source = 'YLSpec'; diagnostic.code = issue.code; issues.push(diagnostic);
    }
    diagnostics.set(document.uri, issues);
    if (explicit) {if (issues.length) void vscode.window.showWarningMessage('YLSpec: ' + result.issue.message); else void vscode.window.showInformationMessage('YLSpec: Document is valid.');}
    return result;
  }
  function schedule(document) {
    if (document.languageId !== 'ylspec') return;
    const key = document.uri.toString(); clearTimeout(timers.get(key));
    timers.set(key, setTimeout(() => {timers.delete(key); void validate(document);}, config(document).get('validation.delay', 350)));
  }
  const selector = {language: 'ylspec'};
  context.subscriptions.push(diagnostics,
    vscode.workspace.onDidOpenTextDocument(schedule),
    vscode.workspace.onDidChangeTextDocument(event => schedule(event.document)),
    vscode.workspace.onDidSaveTextDocument(schedule),
    vscode.workspace.onDidCloseTextDocument(document => {const key = document.uri.toString(); clearTimeout(timers.get(key)); timers.delete(key); diagnostics.delete(document.uri);}),
    vscode.workspace.onDidChangeConfiguration(event => {if (event.affectsConfiguration('ylspec')) for (const document of vscode.workspace.textDocuments) schedule(document);}),
    vscode.commands.registerCommand('ylspec.validate', () => {const document = vscode.window.activeTextEditor?.document; if (document) return validate(document, true);}),
    vscode.commands.registerCommand('ylspec.newDocument', async () => {const document = await vscode.workspace.openTextDocument({language: 'ylspec', content: template}); await vscode.window.showTextDocument(document);}),
    vscode.languages.registerCompletionItemProvider(selector, {
      provideCompletionItems(document, position) {
        if (tableAt(document.getText(new vscode.Range(new vscode.Position(0, 0), position))) !== '_ylspec') return [];
        const prefix = document.lineAt(position.line).text.slice(0, position.character);
        if (!/^\s*[A-Za-z_]*$/.test(prefix)) return [];
        return Object.entries(fields).map(([name, info]) => {const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Property); item.insertText = name + ' = ' + info.value; item.detail = info.detail; return item;});
      }
    }),
    vscode.languages.registerHoverProvider(selector, {
      provideHover(document, position) {
        const line = document.lineAt(position.line).text, match = /^\s*(version|profile|profile_version|requires)\s*=/.exec(line);
        if (!match || position.character > line.indexOf('=') || tableAt(document.getText(new vscode.Range(new vscode.Position(0, 0), position))) !== '_ylspec') return;
        return new vscode.Hover(new vscode.MarkdownString('**`_ylspec.' + match[1] + '`**\n\n' + fields[match[1]].detail));
      }
    }),
    vscode.languages.registerDocumentFormattingEditProvider(selector, {
      async provideDocumentFormattingEdits(document, _options, token) {
        if (!config(document).get('format.enabled', false)) {void vscode.window.showInformationMessage('Enable ylspec.format.enabled to use semantic formatting. It removes comments and changes whitespace.'); return [];}
        const version = document.version, result = await inspect(document, true);
        if (token.isCancellationRequested || document.isClosed || document.version !== version || result.formatted === undefined) return [];
        return [vscode.TextEdit.replace(new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length)), result.formatted)];
      }
    }),
    {dispose() {disposed = true; for (const timer of timers.values()) clearTimeout(timer); timers.clear(); for (const complete of pending.values()) complete({}); pending.clear(); if (worker) void worker.terminate(); worker = undefined;}}
  );
  for (const document of vscode.workspace.textDocuments) schedule(document);
  return {validate};
}
module.exports = {activate};
