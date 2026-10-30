/* Run with Node and Playwright against the scene-graph test fixture viewer.
   node tests/scene/viewer_choices_browser.cjs <test.html> <output-directory>
   No service calls; the input viewer must have g003 through g009 from fixture_graph(). */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

(async () => {
  const out = path.resolve(process.argv[3]);
  await fs.mkdir(out, {recursive:true});
  const browser = await chromium.launch({channel:'msedge', headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}, acceptDownloads:true});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(path.resolve(process.argv[2])).href);
    const choose = async (label,id,route) => {
      await page.getByRole('button',{name:`Select ${label} ${id}`,exact:true}).click();
      await page.getByRole('button',{name:route,exact:true}).click();
    };
    await choose('bowl','g004','Model + Marso texture');
    await page.getByLabel('Notes for this object').fill('Walnut; keep <original> geometry & grain.');
    await page.getByRole('button',{name:'Build modular part',exact:true}).click();
    assert.equal(await page.getByLabel('Notes for this object').inputValue(),'Walnut; keep <original> geometry & grain.');
    await page.getByRole('button',{name:'Model + Marso texture',exact:true}).click();
    await choose('countertop','g003','Build modular part');
    await choose('onion','g005','Generate in Marso');
    await choose('onion','g006','Instance + retexture');
    await page.getByLabel('Mesh name or library asset ID').fill('Existing_Onion');
    await page.getByLabel('Find similar in Marso before making it').uncheck();
    const downloadEvent = page.waitForEvent('download');
    await page.getByRole('button',{name:'Export choices',exact:true}).click();
    const download = await downloadEvent;
    const saved = path.join(out,'scene_choices.json');
    await download.saveAs(saved);
    const doc = JSON.parse(await fs.readFile(saved,'utf8'));
    assert.equal(doc.choices.g004.route,'model');
    assert.equal(doc.choices.g003.route,'kit');
    assert.equal(doc.choices.g005.route,'generate');
    assert.equal(doc.choices.g006.source_ref,'Existing_Onion');
    assert.equal(doc.choices.g006.search_library,false);
    assert.equal(Object.keys(doc.choices).length,4);
    await page.reload();
    assert.match(await page.locator('#choiceCount').textContent(),/^4 /);
    await page.getByRole('button',{name:'Select bowl g004',exact:true}).click();
    assert.equal(await page.getByLabel('Notes for this object').inputValue(),doc.choices.g004.notes);
    await page.getByRole('button',{name:'Remove from plan',exact:true}).click();
    assert.match(await page.locator('#choiceCount').textContent(),/^3 /);
    await page.locator('#choiceFile').setInputFiles(saved);
    await page.waitForFunction(() => document.querySelector('#choiceCount').textContent.startsWith('4 '));
    const bad = {...doc,graph_key:'different-scene'};
    await page.locator('#choiceFile').setInputFiles({name:'stale.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bad))});
    await page.waitForFunction(() => document.querySelector('#choiceStatus').textContent.startsWith('Import rejected'));
    assert.match(await page.locator('#choiceCount').textContent(),/^4 /);
    await page.getByLabel('Editing as',{exact:true}).selectOption('agent');
    await choose('chair','g008','Model + Marso texture');
    assert.match(await page.locator('#choiceCount').textContent(),/^6 /); // uncertain g009 shares it
    await page.getByRole('button',{name:'Apply to repeated objects',exact:true}).click();
    assert.match(await page.locator('#choiceCount').textContent(),/^7 /);
    const secondEvent = page.waitForEvent('download');
    await page.getByRole('button',{name:'Export choices',exact:true}).click();
    await (await secondEvent).saveAs(path.join(out,'repeated_choices.json'));
    const repeated = JSON.parse(await fs.readFile(path.join(out,'repeated_choices.json'),'utf8'));
    assert.equal(repeated.choices.g007.decided_by,'agent');
    await page.getByRole('button',{name:'Select bowl g004',exact:true}).click();
    await page.getByRole('button',{name:'Instance + retexture: Fixture bowl (possible)',exact:true}).click();
    assert.equal(await page.getByLabel('Source type',{exact:true}).inputValue(),'library');
    assert.equal(await page.getByLabel('Mesh name or library asset ID').inputValue(),'fixture-bowl');
    assert.equal(await page.getByLabel('Find similar in Marso before making it').isChecked(),false);
    await page.getByRole('button',{name:'Gallery',exact:true}).click();
    await page.screenshot({path:path.join(out,'choices-desktop.png')});
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(out,'choices-mobile.png'),fullPage:true});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),true);
    assert.deepEqual(errors,[]);
    console.log('Browser checks passed: routes, notes, export/import, stale rejection, storage, identity, repeated objects, agent proposals, library candidate selection, responsive layout.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode=1;});
