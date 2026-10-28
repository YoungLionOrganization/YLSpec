// Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0
import {useEffect, useState} from 'react';
import {createClient} from '../src/web.mjs';
export function MetadataView() {
  const [name, setName] = useState('Loading');
  useEffect(() => {let active = true; void createClient().then(yl => {const doc = new yl.Document({name: 'React browser'}); if (active) setName(String(yl.unpack(yl.pack(doc)).data.name));}); return () => {active = false;};}, []);
  return <output>{name}</output>;
}
