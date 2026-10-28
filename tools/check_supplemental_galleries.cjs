/* Read-only browser QA of frozen supplemental HTML/art. Writes only records/. */
const {chromium}=require('C:/Users/luyua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL,fileURLToPath}=require('url');
const ROOT=path.resolve(__dirname,'..');
const specs=[
 {id:'field-stages',html:'previews/world/field-stages/index.html',manifest:'assets/world/terrain/field-stages/manifest.json'},
 {id:'bridge-railtypes',html:'previews/world/bridge-railtypes/index.html',manifest:'assets/world/infrastructure/bridge-railtypes/manifest.json'},
 {id:'shore-geometry',html:'previews/world/shore-geometry/index.html',manifest:'assets/world/terrain/shore-geometry/manifest.json'},
 {id:'rocks-overlay',html:'previews/world/rocks-overlay/index.html',manifest:'assets/world/terrain/rocks-overlay/manifest.json'}
];
const onlyArg=process.argv.find(a=>a.startsWith('--only='));
const selected=onlyArg?new Set(onlyArg.slice(7).split(',')):new Set(specs.map(s=>s.id));
const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const rel=f=>path.relative(ROOT,f).split(path.sep).join('/');
function localReference(href,base){
 try{const u=new URL(href,base);if(u.protocol!=='file:')return {href,resolved:u.href,local:false};u.hash='';u.search='';const f=fileURLToPath(u);const exists=fs.existsSync(f);return {href,resolved:rel(f),local:true,exists,isFile:exists&&fs.statSync(f).isFile()};}
 catch(e){return {href,local:true,exists:false,error:e.message};}
}
(async()=>{
 const pages=[],checks=[],errors=[],failures=[];
 const executablePath='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
 const browser=await chromium.launch({headless:true,executablePath});const browserVersion=browser.version();
 const add=(id,passed,detail={})=>{const c={id,passed:!!passed,...detail};checks.push(c);if(!c.passed)failures.push(c);return c;};
 for(const spec of specs){
  if(!selected.has(spec.id)){pages.push({...spec,status:'pending-freeze-or-full-run',checks:[]});continue;}
  const full=path.join(ROOT,spec.html),base=pathToFileURL(full).href;
  if(!fs.existsSync(full)){add(spec.id+'.HTMLExists',false,{file:spec.html});pages.push({...spec,status:'failed',checks:[]});continue;}
  const htmlSha256=sha(full),sourceManifest=path.join(ROOT,spec.manifest);
  const item={...spec,htmlSha256,sourceURL:base,manifestSHA256:fs.existsSync(sourceManifest)?sha(sourceManifest):null,status:'checking',viewports:[],errors:[],checks:[]};
  const firstCheck=checks.length;add(spec.id+'.sourceManifestExists',fs.existsSync(sourceManifest),{file:spec.manifest});
  for(const width of [1440,390]){
   const height=width===1440?1000:844;
   const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
   const observed=[];
   page.on('pageerror',e=>observed.push({type:'pageerror',message:e.message}));
   page.on('console',m=>{if(m.type()==='error')observed.push({type:'console-error',message:m.text()});});
   page.on('requestfailed',r=>observed.push({type:'requestfailed',url:r.url(),message:r.failure()?.errorText}));
   page.on('response',r=>{if(r.status()>=400)observed.push({type:'http-error',url:r.url(),status:r.status()});});
   await page.goto(base,{waitUntil:'load',timeout:30000});
   const initialLayout=await page.evaluate(()=>({scrollWidth:document.documentElement.scrollWidth,viewportWidth:innerWidth}));
   add(spec.id+'.'+width+'.initialNoHorizontalOverflow',initialLayout.scrollWidth<=width,initialLayout);
   // Expanding disclosure panels and changing lazy-loading is transient browser state only.
   await page.evaluate(()=>{document.querySelectorAll('details').forEach(d=>d.open=true);document.querySelectorAll('img').forEach(i=>i.loading='eager');});
   let loadTimeout=null;
   try{await page.waitForFunction(()=>Array.from(document.images).every(i=>i.complete),null,{timeout:20000});}catch(e){loadTimeout=e.message;}
   const content=await page.evaluate(()=>({
    images:Array.from(document.images).map(i=>({src:i.getAttribute('src'),resolved:i.currentSrc||i.src,complete:i.complete,naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,alt:i.alt})),
    hrefs:Array.from(document.querySelectorAll('[href]')).map(a=>a.getAttribute('href')),
    layout:{scrollWidth:document.documentElement.scrollWidth,viewportWidth:innerWidth},detailsOpened:document.querySelectorAll('details[open]').length
   }));
   const images=content.images.map(i=>{const local=localReference(i.resolved,base);return {...i,...local,sha256:local.local&&local.exists&&local.isFile?sha(path.join(ROOT,local.resolved)):null};});
   const localHrefs=Array.from(new Set(content.hrefs)).map(h=>localReference(h,base)).filter(h=>h.local);
   add(spec.id+'.'+width+'.allActualImagesLoad',loadTimeout===null&&images.length>0&&images.every(i=>i.complete&&i.naturalWidth>0&&i.naturalHeight>0),{imageCount:images.length,loadTimeout,broken:images.filter(i=>!i.complete||!i.naturalWidth||!i.naturalHeight)});
   add(spec.id+'.'+width+'.allLocalHrefsExist',localHrefs.every(h=>h.exists),{localHrefCount:localHrefs.length,missing:localHrefs.filter(h=>!h.exists)});
   add(spec.id+'.'+width+'.expandedNoHorizontalOverflow',content.layout.scrollWidth<=width,content.layout);
   const screenshot='records/supplemental-gallery-'+spec.id+'-'+width+'.png';
   await page.screenshot({path:path.join(ROOT,screenshot),fullPage:false});
   add(spec.id+'.'+width+'.noJavaScriptConsoleOrNetworkErrors',observed.length===0,{errors:observed});
   item.viewports.push({width,height,initialLayout,expandedLayout:content.layout,detailsOpened:content.detailsOpened,images,localHrefs,screenshot:{file:screenshot,sha256:sha(path.join(ROOT,screenshot)),sourceHTML:spec.html,sourceHTMLSha256:htmlSha256,sourceURL:base,browserState:'all details opened;all img eager;viewport screenshot;source files unmodified'}});
   item.errors.push(...observed.map(e=>({width,...e})));await page.close();
  }
  add(spec.id+'.HTMLUnchangedDuringCheck',sha(full)===htmlSha256,{file:spec.html});
  add(spec.id+'.manifestUnchangedDuringCheck',fs.existsSync(sourceManifest)&&sha(sourceManifest)===item.manifestSHA256,{file:spec.manifest});
  item.checks=checks.slice(firstCheck);item.status=item.checks.every(c=>c.passed)?'passed':'failed';errors.push(...item.errors.map(e=>({page:spec.id,...e})));pages.push(item);
 }
 await browser.close();
 const pendingPages=pages.filter(p=>p.status==='pending-freeze-or-full-run').map(p=>p.id);
 const report={createdAt:new Date().toISOString(),schema:'supplemental-gallery-browser-validation.v1',tool:{file:rel(__filename),sha256:sha(__filename),browser:'Edge Chromium',version:browserVersion,executablePath,headless:true},complete:failures.length===0&&pendingPages.length===0,phase:pendingPages.length?'partial-frozen-pages':'all-four-final-pages',readOnlyHTMLAndArt:true,requiredPages:specs.map(s=>s.id),pendingPages,passed:checks.filter(c=>c.passed).length,failed:failures.length,checks,pages,errors,failures,scope:'Actual local HTML in headless Edge at1440/390;all img including closed lazy details forced to load;all local href existence;initial+expanded horizontal overflow;page/console/network errors;current source SHA and screenshots',localVisualPassed:null,visualScopeNote:'Browser loading/layout checks;does not replace each pack actual artwork review,source coverage audit or Unity validation',userArtAcceptance:'pending',unityValidated:false};
 fs.writeFileSync(path.join(ROOT,'records/supplemental-gallery-browser-validation.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({complete:report.complete,phase:report.phase,passed:report.passed,failed:report.failed,pendingPages,pages:pages.map(p=>({id:p.id,status:p.status,htmlSha256:p.htmlSha256,manifestSHA256:p.manifestSHA256,images:p.viewports?.[0]?.images.length})),errors,failures}));
 if(failures.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
