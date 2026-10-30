/* Read-only local brand-page QA. Only records/ reports and screenshots are written. */
const {chromium}=require('C:/Users/luyua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL,fileURLToPath}=require('url');
const ROOT=path.resolve(__dirname,'..');
const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,f))).digest('hex');
const local=(url,base)=>{const u=new URL(url,base),fragment=u.hash.slice(1);if(u.protocol!=='file:')return {url:u.href,local:false,fragment};u.hash='';u.search='';const full=fileURLToPath(u);return {file:path.relative(ROOT,full).split(path.sep).join('/'),local:true,exists:fs.existsSync(full),fragment};};
(async()=>{
 const html='previews/branding/index.html',manifest='docs/asset-branding-manifest.json',packageManifest='branding/yuntu-wanli/manifest.json',base=pathToFileURL(path.join(ROOT,html)).href;
 const htmlSha256=sha(html),manifestSha256=sha(manifest),assets=JSON.parse(fs.readFileSync(path.join(ROOT,manifest),'utf8'));
 const inputs=assets.map(a=>({id:a.id,file:a.file,expectedSHA256:a.sha256,sha256:sha(a.file),width:a.width,height:a.height}));
 const inputSnapshots=[html,packageManifest,manifest,...inputs.map(a=>a.file)].map(file=>({file,sha256:sha(file)}));
 const checks=[],errors=[],viewports=[];
 const test=(id,passed,detail={})=>checks.push({id,passed:!!passed,...detail});
 const executablePath='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
 const browser=await chromium.launch({headless:true,executablePath,args:['--no-first-run']});
 const browserVersion=browser.version();
 const ui=JSON.parse(fs.readFileSync(path.join(ROOT,'docs/UI_MASTER_MANIFEST.json'),'utf8'));
 const screens=new Map(ui.screens.map(s=>[s.id,s]));
 for(const width of [1440,390]){
  const height=width===1440?1080:844,page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1}),events=[];
  page.on('pageerror',e=>events.push({type:'pageerror',message:e.message}));
  page.on('console',m=>{if(m.type()==='error')events.push({type:'console-error',message:m.text()});});
  page.on('requestfailed',r=>events.push({type:'requestfailed',url:r.url(),error:r.failure()?.errorText}));
  page.on('response',r=>{if(r.status()>=400)events.push({type:'http-error',url:r.url(),status:r.status()});});
  await page.goto(base,{waitUntil:'load'});await page.evaluate(()=>document.querySelectorAll('img').forEach(i=>i.loading='eager'));
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete),null,{timeout:20000});
  const data=await page.evaluate(()=>({
   title:document.title,heading:document.querySelector('h1')?.textContent,
   images:[...document.images].map(i=>({src:i.currentSrc||i.src,complete:i.complete,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,displayWidth:i.getBoundingClientRect().width,displayHeight:i.getBoundingClientRect().height})),
   mainLogos:[...document.querySelectorAll('[data-main-logo]')].map(i=>({src:i.currentSrc||i.src,complete:i.complete,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,displayWidth:i.getBoundingClientRect().width,displayHeight:i.getBoundingClientRect().height})),
   icons:[...document.querySelectorAll('.iconline img')].map(i=>({src:i.currentSrc||i.src,complete:i.complete,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight})),
   downloads:[...document.querySelectorAll('.grid article a[download]')].map(a=>a.href),
   screenLinks:[...document.querySelector('main>section:last-child nav').querySelectorAll('a')].map(a=>a.href),
   hrefs:[...document.querySelectorAll('[href]')].map(a=>a.href),scrollWidth:document.documentElement.scrollWidth,viewportWidth:innerWidth
  }));
  const allImages=data.images.map(i=>({...i,...local(i.src,base)}));
  const hrefs=data.hrefs.map(h=>local(h,base)).filter(h=>h.local);
  const downloads=data.downloads.map(h=>local(h,base));
  const screenLinks=data.screenLinks.map(h=>{const ref=local(h,base),screen=screens.get(ref.fragment);const design=screen?.designPath||screen?.design||screen?.image||screen?.designFile;return {...ref,screenInCurrentCatalog:!!screen,design:design||null,designExists:design?fs.existsSync(path.join(ROOT,design)):false};});
  test(width+'.formalTitle',data.title.includes('云途万里')&&!data.title.includes('暂名')&&data.heading.includes('云途万里'));
  test(width+'.twoActualMainLogos',data.mainLogos.length===2&&data.mainLogos.every(i=>i.complete&&i.naturalWidth===1860&&i.naturalHeight===845),{count:data.mainLogos.length});
  test(width+'.mainLogosPreserveAspect',data.mainLogos.every(i=>Math.abs(i.displayWidth/i.displayHeight-1860/845)<.01));
  test(width+'.threeActualIconSizes',data.icons.length===3&&JSON.stringify(data.icons.map(i=>[i.naturalWidth,i.naturalHeight]))===JSON.stringify([[256,256],[128,128],[64,64]]));
  test(width+'.eightFormalPNGDownloadLinks',downloads.length===8&&new Set(downloads.map(d=>d.file)).size===8&&downloads.every(d=>d.exists)&&inputs.every(a=>downloads.some(d=>d.file===a.file)),{count:downloads.length});
  test(width+'.fourCurrentScreenLinks',screenLinks.length===4&&JSON.stringify(screenLinks.map(l=>l.fragment))===JSON.stringify(['01-main-menu','02-bootstrap','09-main-hud','123-about'])&&screenLinks.every(l=>l.exists&&l.screenInCurrentCatalog&&l.designExists),{links:screenLinks});
  test(width+'.allThirteenActualImagesLoad',allImages.length===13&&allImages.every(i=>i.complete&&i.naturalWidth>0&&i.naturalHeight>0&&i.exists),{count:allImages.length});
  test(width+'.allLocalHrefsExist',hrefs.every(h=>h.exists),{count:hrefs.length,missing:hrefs.filter(h=>!h.exists)});
  test(width+'.noHorizontalOverflow',data.scrollWidth<=width,{scrollWidth:data.scrollWidth,viewportWidth:width});
  const file='records/brand-gallery-'+(width===1440?'desktop':'mobile')+'.png';await page.screenshot({path:path.join(ROOT,file),fullPage:false});
  test(width+'.noPageConsoleOrNetworkErrors',events.length===0,{errors:events});
  viewports.push({width,height,title:data.title,images:allImages,mainLogos:data.mainLogos,iconSizes:data.icons,downloadLinks:downloads,screenLinks,localHrefs:hrefs,screenshot:{file,sha256:sha(file),sourceHTML:html,sourceHTMLSha256:htmlSha256,sourceURL:base,viewport:[width,height]}});
  errors.push(...events.map(e=>({width,...e})));await page.close();
 }
 await browser.close();
 test('eightCurrentManifestPNGSHA',inputs.length===8&&inputs.every(a=>a.sha256===a.expectedSHA256),{count:inputs.length});
 test('HTMLUnchangedDuringCheck',sha(html)===htmlSha256);
 test('manifestUnchangedDuringCheck',sha(manifest)===manifestSha256);
 test('eightPNGUnchangedDuringCheck',inputs.every(a=>sha(a.file)===a.sha256));
 test('allTrackedInputsUnchangedDuringCheck',inputSnapshots.every(s=>sha(s.file)===s.sha256));
 const failures=checks.filter(c=>!c.passed),result={createdAt:new Date().toISOString(),schema:'brand-gallery-browser-validation.v1',complete:failures.length===0,html,htmlSha256,manifest,manifestSha256,assets:inputs,inputSnapshots,passed:failures.length===0,passedChecks:checks.length-failures.length,failed:failures.length,checks,errors,pageErrors:errors.filter(e=>e.type==='pageerror'||e.type==='console-error'),failedRequests:errors.filter(e=>e.type==='requestfailed'||e.type==='http-error'),failures,viewports,browser:{name:'Edge Chromium',version:browserVersion,headless:true,executablePath},localVisualPassed:null,scope:'Actual file:// brand page at1440/390;2hero logos,3icon sizes,8formal PNG downloads,4screen targets,all local href/img,current sourceSHA and viewport screenshots;HTML/art never rewritten',userArtAcceptance:'pending',unityValidated:false};
 fs.writeFileSync(path.join(ROOT,'records/brand-gallery-browser-validation.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({complete:result.complete,passed:result.passed,passedChecks:result.passedChecks,failed:result.failed,htmlSha256,manifestSha256,errors,failures}));if(failures.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
