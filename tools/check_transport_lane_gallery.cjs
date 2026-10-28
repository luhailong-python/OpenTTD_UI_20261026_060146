const fs=require('fs'),path=require('path'),http=require('http'),crypto=require('crypto');
const {chromium}=require('C:/Users/luyua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),output=path.join(root,'records/world-production');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const rel=p=>path.relative(root,p).replaceAll('\\','/');
(async()=>{
 const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);const p=path.resolve(root,'.'+pathname);
  if(!p.startsWith(root+path.sep)){res.statusCode=403;res.end();return;}
  if(!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.statusCode=404;res.end();return;}
  res.setHeader('Content-Type',({'.png':'image/png','.jpg':'image/jpeg','.html':'text/html; charset=utf-8'})[path.extname(p)]||'application/octet-stream');fs.createReadStream(p).pipe(res);
 });await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const url=`http://127.0.0.1:${server.address().port}/previews/world/transport-lanes/index.html`;await page.goto(url,{waitUntil:'networkidle'});
 await page.evaluate(()=>document.querySelectorAll('img').forEach(i=>i.loading='eager'));await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
 const checks=[];const check=(id,ok,detail)=>checks.push({id,level:ok?'OK':'FAIL',detail});
 check('all-17-state-and-detail-pages-load',await page.locator('img').count()===17);
 check('desktop-no-overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 check('actual-72-tunnel-and-all-bridge-source-caption',await page.locator('p').innerText().then(s=>s.includes('72')&&s.includes('13')));
 check('all-image-links-return-200',await page.locator('figure a').evaluateAll(as=>as.every(a=>a.getAttribute('href')===a.querySelector('img').getAttribute('src'))));
 const screenshots=[];
 async function screenshot(name){const p=path.join(output,name+'.png');await page.screenshot({path:p});screenshots.push({file:rel(p),sha256:hash(p)});fs.writeFileSync(p+'.derivation.json',JSON.stringify({operation:'Actual Edge browser screenshot of local static PNG gallery; QA only, not generated game art',capturedAt:new Date().toISOString(),derivedFrom:[{file:'previews/world/transport-lanes/index.html',sha256:hash(path.join(root,'previews/world/transport-lanes/index.html'))}]},null,2));}
 await screenshot('transport-lane-gallery-desktop');await page.locator('figure').nth(3).scrollIntoViewIfNeeded();await screenshot('transport-lane-gallery-bridge');
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>scrollTo(0,0));
 check('mobile-no-overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await screenshot('transport-lane-gallery-mobile');
 check('browser-no-javascript-errors',errors.length===0,errors);
 const result={createdAt:new Date().toISOString(),checks,failures:checks.filter(c=>c.level==='FAIL'),screenshots,gallerySHA256:hash(path.join(root,'previews/world/transport-lanes/index.html')),limitations:'Browser QA verifies display and available links only; static lane/structure assembly is independently checked by PNG RGBA checks and visual review. Unity not run.'};
 fs.writeFileSync(path.join(output,'transport-lane-browser-validation.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({checks:checks.length,failures:result.failures.length}));await browser.close();await new Promise(r=>server.close(r));
})().catch(e=>{console.error(e);process.exitCode=1;});
