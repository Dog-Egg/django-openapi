(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[85],{14247:(e,t,n)=>{"use strict";n.r(t),n.d(t,{default:()=>m});var r=n(67294),s=n(86010),a=n(1944),i=n(35281),o=n(80215),p=n(45042),c=n(39407);const l="mdxPageWrapper_j9I6";function m(e){const{content:t}=e,{metadata:{title:n,description:m,frontMatter:d}}=t,{wrapperClassName:u,hide_table_of_contents:g}=d;return r.createElement(a.FG,{className:(0,s.Z)(u??i.k.wrapper.mdxPages,i.k.page.mdxPage)},r.createElement(a.d,{title:n,description:m}),r.createElement(o.Z,null,r.createElement("main",{className:"container container--fluid margin-vert--lg"},r.createElement("div",{className:(0,s.Z)("row",l)},r.createElement("div",{className:(0,s.Z)("col",!g&&"col--8")},r.createElement("article",null,r.createElement(p.Z,null,r.createElement(t,null)))),!g&&t.toc.length>0&&r.createElement("div",{className:"col col--2"},r.createElement(c.Z,{toc:t.toc,minHeadingLevel:d.toc_min_heading_level,maxHeadingLevel:d.toc_max_heading_level}))))))}},35340:(e,t,n)=>{"use strict";n.d(t,{Z:()=>f});var r=n(22435),s=n(67294),a=n(86010);const i="browserWindow_my1Q",o="browserWindowHeader_jXSR",p="buttons_uHc7",c="browserWindowAddressBar_Pd8y",l="dot_giz1",m="browserWindowMenuIcon_Vhuh",d="bar_rrRL",u="browserWindowBody_Idgs";function g(e){let{children:t,minHeight:n,url:r="http://localhost:3000"}=e;return s.createElement("div",{className:i,style:{minHeight:n}},s.createElement("div",{className:o},s.createElement("div",{className:p},s.createElement("span",{className:l,style:{background:"#f25f58"}}),s.createElement("span",{className:l,style:{background:"#fbbe3c"}}),s.createElement("span",{className:l,style:{background:"#58cb42"}})),s.createElement("div",{className:(0,a.Z)(c,"text--truncate")},r),s.createElement("div",{className:m},s.createElement("div",null,s.createElement("span",{className:d}),s.createElement("span",{className:d}),s.createElement("span",{className:d})))),s.createElement("div",{className:u},t))}const h="iframe_hLeN";var y=n(23612);const f={...r.Z,BrowserWindow:g,SwaggerUI:function(e){let{spec:t,height:r=450}=e;return s.createElement(g,{url:"http://127.0.0.1:8000/docs/"},s.createElement("iframe",{className:h,style:{height:r},srcDoc:n(5607).Z.replace("'{{spec}}'",JSON.stringify(n(41764)(`./${t}.json`)))}))},UnderConstruction:function(){return s.createElement("div",null,s.createElement(y.Z,{type:"caution",title:"\u6ce8\u610f"},"\ud83d\udea7 \u5f53\u524d\u9875\u6587\u6863\u8fd8\u5728\u65bd\u5de5\u4e2d\uff0c\u5e76\u672a\u63d0\u4f9b\u5b8c\u6574\u7684\u4f7f\u7528\u8bf4\u660e\uff01 \ud83d\udea7"))}}},5607:(e,t,n)=>{"use strict";n.d(t,{Z:()=>r});const r='<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device-width, initial-scale=1"/>\n    <meta\n            name="description"\n            content="SwaggerUI"\n    />\n    <title>SwaggerUI</title>\n    <style>\n        body {\n            margin: 0;\n        }\n    </style>\n    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css"/>\n</head>\n<body>\n<div id="swagger-ui"></div>\n<script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js" crossorigin><\/script>\n<script>\n    window.onload = () => {\n        window.ui = SwaggerUIBundle({\n            spec: \'{{spec}}\',\n            dom_id: \'#swagger-ui\',\n            requestInterceptor: function (request) {\n                return request;\n            },\n            responseInterceptor: function (response) {\n                response.text = \'\u8fd9\u662f\u4e2a\u6587\u6863\uff0c\u8bf7\u62f7\u8d1d\u4ee3\u7801\u81ea\u884c\u6d4b\u8bd5\uff01\';\n                return response;\n            }\n        });\n    };\n<\/script>\n</body>\n</html>\n'},41764:(e,t,n)=>{var r={"./parameter_styles.json":24252,"./path_parameter.json":42955,"./path_parameter_type.json":6868,"./query_parameter.json":74857,"./query_parameter_blank.json":73829,"./query_parameter_default.json":68094,"./response.json":97119,"./\u5f00\u59cb.json":82449};function s(e){var t=a(e);return n(t)}function a(e){if(!n.o(r,e)){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t}return r[e]}s.keys=function(){return Object.keys(r)},s.resolve=a,e.exports=s,s.id=41764},24252:e=>{"use strict";e.exports=JSON.parse('{"openapi":"3.0.3","info":{"title":"API Document","version":"0.1.0"},"paths":{"/path":{"get":{"parameters":[{"name":"a","in":"query","required":true,"schema":{"type":"array","items":{"nullable":true}},"style":"form","explode":true},{"name":"b","in":"query","required":true,"schema":{"type":"array","items":{"nullable":true}},"style":"pipeDelimited","explode":false}],"responses":{"200":{"description":"OK"}}}}}}')},42955:e=>{"use strict";e.exports=JSON.parse('{"openapi":"3.0.3","info":{"title":"API Document","version":"0.1.0"},"paths":{"/path/{id}":{"get":{"parameters":[{"name":"id","in":"path","required":true,"schema":{"type":"string"},"style":"simple","explode":false}],"responses":{"200":{"description":"OK"}}}}}}')},6868:e=>{"use strict";e.exports=JSON.parse('{"openapi":"3.0.3","info":{"title":"API Document","version":"0.1.0"},"paths":{"/path/{id}":{"post":{"parameters":[{"name":"id","in":"path","required":true,"schema":{"type":"integer"},"style":"simple","explode":false}],"responses":{"200":{"description":"OK"}}}}}}')},74857:e=>{"use strict";e.exports=JSON.parse('{"openapi":"3.0.3","info":{"title":"API Document","version":"0.1.0"},"paths":{"/foo":{"get":{"parameters":[{"name":"a","in":"query","required":true,"description":"\u53c2\u6570A","schema":{"type":"integer","description":"\u53c2\u6570A"},"style":"form","explode":true},{"name":"b","in":"query","description":"\u53c2\u6570B","schema":{"type":"array","description":"\u53c2\u6570B","items":{"type":"integer"}},"style":"form","explode":true}],"responses":{"200":{"description":"OK"}}}}}}')},73829:e=>{"use strict";e.exports=JSON.parse('{"openapi":"3.0.3","info":{"title":"API Document","version":"0.1.0"},"paths":{"/path":{"get":{"parameters":[{"name":"a","in":"query","schema":{"type":"string"},"style":"form","explode":true},{"name":"b","in":"query","schema":{"type":"string"},"style":"form","explode":true,"allowEmptyValue":true}],"responses":{"200":{"description":"OK"}}}}}}')},68094:e=>{"use strict";e.exports=JSON.parse('{"openapi":"3.0.3","info":{"title":"API Document","version":"0.1.0"},"paths":{"/path":{"get":{"parameters":[{"name":"a","in":"query","schema":{"type":"integer","default":1},"style":"form","explode":true}],"responses":{"200":{"description":"OK"}}}}}}')},97119:e=>{"use strict";e.exports=JSON.parse('{"openapi":"3.0.3","info":{"title":"API Document","version":"0.1.0"},"paths":{"/path":{"get":{"responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","properties":{"name":{"type":"string","description":"\u59d3\u540d"},"age":{"type":"integer","description":"\u5e74\u9f84","maximum":0}}}}}}}}},"/users/{uid}":{"get":{"parameters":[{"name":"uid","in":"path","required":true,"schema":{"type":"string"},"style":"simple","explode":false}],"summary":"\u83b7\u53d6\u7528\u6237\u4fe1\u606f","responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"$ref":"#/components/schemas/fcc63f60.UserSchema"}}}}}}}},"components":{"schemas":{"fcc63f60.UserSchema":{"type":"object","properties":{"id":{"type":"integer","description":"ID","readOnly":true},"password":{"type":"string","description":"\u5bc6\u7801","maxLength":128},"last_login":{"type":"string","description":"\u4e0a\u6b21\u767b\u5f55","nullable":true,"format":"date-time"},"is_superuser":{"type":"boolean","default":false,"description":"\u8d85\u7ea7\u7528\u6237\u72b6\u6001\\n\\n_\u6307\u660e\u8be5\u7528\u6237\u7f3a\u7701\u62e5\u6709\u6240\u6709\u6743\u9650\u3002_"},"username":{"type":"string","description":"\u7528\u6237\u540d\\n\\n_\u5fc5\u586b\uff1b\u957f\u5ea6\u4e3a150\u4e2a\u5b57\u7b26\u6216\u4ee5\u4e0b\uff1b\u53ea\u80fd\u5305\u542b\u5b57\u6bcd\u3001\u6570\u5b57\u3001\u7279\u6b8a\u5b57\u7b26\u201c@\u201d\u3001\u201c.\u201d\u3001\u201c-\u201d\u548c\u201c_\u201d\u3002_","maxLength":150},"first_name":{"type":"string","description":"\u540d\u5b57","maxLength":150},"last_name":{"type":"string","description":"\u59d3\u6c0f","maxLength":150},"email":{"type":"string","description":"\u7535\u5b50\u90ae\u4ef6\u5730\u5740","maxLength":254},"is_staff":{"type":"boolean","default":false,"description":"\u5de5\u4f5c\u4eba\u5458\u72b6\u6001\\n\\n_\u6307\u660e\u7528\u6237\u662f\u5426\u53ef\u4ee5\u767b\u5f55\u5230\u8fd9\u4e2a\u7ba1\u7406\u7ad9\u70b9\u3002_"},"is_active":{"type":"boolean","default":true,"description":"\u6709\u6548\\n\\n_\u6307\u660e\u7528\u6237\u662f\u5426\u88ab\u8ba4\u4e3a\u662f\u6d3b\u8dc3\u7684\u3002\u4ee5\u53cd\u9009\u4ee3\u66ff\u5220\u9664\u5e10\u53f7\u3002_"},"date_joined":{"type":"string","description":"\u52a0\u5165\u65e5\u671f","format":"date-time"}},"title":"UserSchema"}}}}')},82449:e=>{"use strict";e.exports=JSON.parse('{"openapi":"3.0.3","info":{"title":"API Document","version":"0.1.0"},"paths":{"/path":{"get":{"responses":{"200":{"description":"OK"}}}}},"servers":[{"url":"/api"}]}')}}]);