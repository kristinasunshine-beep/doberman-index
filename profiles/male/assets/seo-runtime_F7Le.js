(function(global){
  "use strict";
  let manifestPromise;
  const setMeta=(selector,attribute,value)=>{
    if(!value)return;
    let node=document.head.querySelector(selector);
    if(!node){node=document.createElement("meta");const match=selector.match(/meta\[(name|property)="([^"]+)"\]/);if(match)node.setAttribute(match[1],match[2]);document.head.append(node)}
    node.setAttribute(attribute,value);
  };
  const setCanonical=value=>{
    if(!value)return;
    let node=document.head.querySelector('link[rel="canonical"]');
    if(!node){node=document.createElement("link");node.rel="canonical";document.head.append(node)}
    node.href=value;
  };
  const loadManifest=base=>manifestPromise||(manifestPromise=fetch(new URL("data/seo-manifest.json",base),{cache:"no-store"}).then(response=>{if(!response.ok)throw new Error("SEO manifest unavailable");return response.json()}));
  function apply(metadata){
    if(!metadata)return false;
    document.title=metadata.title;
    setMeta('meta[name="description"]',"content",metadata.description);
    setCanonical(metadata.canonical);
    setMeta('meta[property="og:type"]',"content","website");
    setMeta('meta[property="og:site_name"]',"content","Doberman Index");
    setMeta('meta[property="og:title"]',"content",metadata.title);
    setMeta('meta[property="og:description"]',"content",metadata.description);
    setMeta('meta[property="og:url"]',"content",metadata.canonical);
    if(metadata.image)setMeta('meta[property="og:image"]',"content",metadata.image);
    setMeta('meta[name="twitter:card"]',"content",metadata.image?"summary_large_image":"summary");
    setMeta('meta[name="twitter:title"]',"content",metadata.title);
    setMeta('meta[name="twitter:description"]',"content",metadata.description);
    if(metadata.image)setMeta('meta[name="twitter:image"]',"content",metadata.image);
    const old=document.head.querySelector('script[data-seo-jsonld]');if(old)old.remove();
    if(metadata.json_ld){const node=document.createElement("script");node.type="application/ld+json";node.dataset.seoJsonld="record";node.textContent=JSON.stringify(metadata.json_ld);document.head.append(node)}
    return true;
  }
  async function applyRecord(recordId,base=document.baseURI){const manifest=await loadManifest(base);return apply(manifest.records?.[recordId])}
  function noindex(){setMeta('meta[name="robots"]',"content","noindex,follow")}
  global.DISEO={apply,applyRecord,noindex,loadManifest};
})(window);
