const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");

class Node{
  constructor(tag){this.tagName=tag.toLowerCase();this.attributes={};this.dataset={};this.textContent="";this.parent=null}
  setAttribute(name,value){this.attributes[name]=String(value)}
  getAttribute(name){return this.attributes[name]??(name==="rel"?this.rel:undefined)}
  remove(){if(this.parent)this.parent.nodes=this.parent.nodes.filter(node=>node!==this)}
}
const selectorMatches=(node,selector)=>{
  if(selector==='link[rel="canonical"]')return node.tagName==="link"&&node.rel==="canonical";
  if(selector==='script[data-seo-jsonld]')return node.tagName==="script"&&node.dataset.seoJsonld;
  const match=selector.match(/^meta\[(name|property)="([^"]+)"\]$/);
  return Boolean(match&&node.tagName==="meta"&&node.attributes[match[1]]===match[2]);
};
const head={nodes:[],querySelector(selector){return this.nodes.find(node=>selectorMatches(node,selector))||null},append(node){node.parent=this;this.nodes.push(node)}};
const document={title:"",baseURI:"https://doberman-index.com/",head,createElement:tag=>new Node(tag)};
const metadata={title:"DION DANTE · DI-M-000001 · Doberman Index",description:"Published record description.",canonical:"https://doberman-index.com/records/DI-M-000001/",image:"https://doberman-index.com/media/dobermans/DI-M-000001/hero.png",json_ld:{"@context":"https://schema.org","@type":"WebPage"}};
let fetchCount=0;
const context={window:{},document,URL,fetch:async()=>{fetchCount++;return{ok:true,json:async()=>({records:{"DI-M-000001":metadata}})}}};
vm.runInNewContext(fs.readFileSync("assets/js/seo-runtime.js","utf8"),context);

(async()=>{
  assert.equal(await context.window.DISEO.applyRecord("DI-M-000001"),true);
  assert.equal(document.title,metadata.title);
  assert.equal(head.querySelector('meta[name="description"]').getAttribute("content"),metadata.description);
  assert.equal(head.querySelector('link[rel="canonical"]').href,metadata.canonical);
  assert.equal(head.querySelector('meta[property="og:url"]').getAttribute("content"),metadata.canonical);
  assert.equal(head.querySelector('meta[name="twitter:card"]').getAttribute("content"),"summary_large_image");
  assert.deepEqual(JSON.parse(head.querySelector('script[data-seo-jsonld]').textContent),metadata.json_ld);
  await context.window.DISEO.applyRecord("DI-M-000001");
  assert.equal(fetchCount,1,"SEO manifest must be cached during one page lifecycle");
  assert.equal(head.nodes.filter(node=>node.tagName==="link"&&node.rel==="canonical").length,1,"only one canonical link is allowed");
  context.window.DISEO.noindex();
  assert.equal(head.querySelector('meta[name="robots"]').getAttribute("content"),"noindex,follow");
  console.log("SEO browser metadata runtime PASS (canonical, description, Open Graph, Twitter and JSON-LD)");
})().catch(error=>{console.error(error);process.exit(1)});
