const {chromium}=require('C:/Users/luyua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
(async()=>{
 const root=path.resolve(__dirname,'..'),checks=[],errors=[],failed=[];
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',args:['--no-first-run']});
 const page=await browser.newPage({viewport:{width:1920,height:1080}});page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(r.url()));
 await page.goto('file:///'+path.join(root,'previews/world/airports/index.html').replaceAll('\\','/'),{waitUntil:'networkidle'});
 checks.push({id:'tenOriginalAirports',passed:await page.locator('#grid article').count()===10});
 checks.push({id:'animationControlsHiddenOnLayouts',passed:!(await page.locator('.animationControls').isVisible())});
 await page.locator('#grid img').evaluateAll(es=>es.forEach(e=>e.loading='eager'));
 await page.waitForFunction(()=>[...document.querySelectorAll('#grid img')].every(i=>i.complete&&i.naturalWidth>0));
 checks.push({id:'allTenFullLayoutPNGsLoad',passed:true});
 await page.screenshot({path:path.join(root,'records/world-production/airport-gallery-desktop.png'),fullPage:false});
 await page.locator('[data-tab=tiles]').click();checks.push({id:'all74SourceTileCards',passed:await page.locator('#grid article').count()===74});
 await page.locator('#search').fill('airport-tile-32-radio');await page.waitForTimeout(100);checks.push({id:'distinctTransmitterSearch',passed:await page.locator('#grid article').count()===1});
 await page.waitForFunction(()=>[...document.querySelectorAll('#grid img')].every(i=>i.complete&&i.naturalWidth===512));
 await page.locator('[data-tab=animations]').click();checks.push({id:'twoDerivativeAnimationClips',passed:await page.locator('#grid article').count()===2});
 const src=await page.locator('#grid img').first().getAttribute('src');await page.waitForTimeout(350);checks.push({id:'actualFrameCycleAdvances',passed:(await page.locator('#grid img').first().getAttribute('src'))!==src});
 await page.locator('#pause').click();const hold=await page.locator('#grid img').first().getAttribute('src');await page.waitForTimeout(350);checks.push({id:'pauseRetainsFrame',passed:(await page.locator('#grid img').first().getAttribute('src'))===hold});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(root,'records/world-production/airport-gallery-mobile.png'),fullPage:false});checks.push({id:'390pxNoHorizontalOverflow',passed:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)});
 await browser.close();
 const result={time:new Date().toISOString(),scope:'offline art inspection gallery only; no Unity or traffic runtime',checks,pageErrors:errors,failedRequests:failed,passed:checks.every(c=>c.passed)&&!errors.length&&!failed.length};fs.writeFileSync(path.join(root,'records/world-production/airport-browser-validation.json'),JSON.stringify(result,null,2));
 for(const name of ['airport-gallery-desktop.png','airport-gallery-mobile.png']){const p=path.join(root,'records/world-production',name);const r={file:'records/world-production/'+name,sha256:crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex'),operation:'headless Edge screenshot of local artwork gallery; capture, not model generation',derivedFrom:[{file:'previews/world/airports/index.html',sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'previews/world/airports/index.html'))).digest('hex')}],nativeModelGeneration:false};fs.writeFileSync(p+'.derivation.json',JSON.stringify(r,null,2))}
 console.log(JSON.stringify(result))
})().catch(e=>{console.error(e);process.exit(1)});
