# Livonian Keyboard Bookmarklet

Just right-click on the `Activate Livonian Keyboard Layout` link below and select "Add to bookmarks" or drag the link to your bookmarks bar.

[Activate Livonian Keyboard Layout](javascript:!function(){if(window.livonianKeyboardActive)return void console.info("Livonian keyboard is already active");const e={"'":{q:"ä",w:"ü",e:"ē",r:"ŗ",t:"ţ",y:"ȳ",u:"ū",i:"ī",o:"ō",p:"ǫ",a:"ā",s:"š",d:"ḑ",g:"ģ",j:"ȯ",k:"ķ",l:"ļ",z:"ž",x:"ö",c:"č",n:"ņ",m:"õ",Q:"Ä",W:"Ü",E:"Ē",R:"Ŗ",T:"Ţ",Y:"Ȳ",U:"Ū",I:"Ī",O:"Ō",P:"Ǫ",A:"Ā",S:"Š",D:"Ḑ",G:"Ģ",J:"Ȯ",K:"Ķ",L:"Ļ",Z:"Ž",X:"Ö",C:"Č",N:"Ņ",M:"Õ"},"`":{q:"ǟ",w:"ǖ",j:"ȱ",x:"ȫ",m:"ȭ",p:"ǭ",Q:"Ǟ",W:"Ǖ",J:"Ȱ",X:"Ȫ",M:"Ȭ",P:"Ǭ"}};let n=null;document.addEventListener("keydown",(function(i){if(1===i.key.length)if(n){if(void 0!==e[n][i.key]){!function(e){const n=document.activeElement;if(n&&void 0!==n.value){const i=n.selectionStart,t=n.selectionEnd;n.value=n.value.substring(0,i)+e+n.value.substring(t),n.setSelectionRange(i+1,i+1)}else document.execCommand("insertText",!1,e)}(e[n][i.key]),i.preventDefault()}n=null}else void 0!==e[i.key]&&(n=i.key,i.preventDefault())})),window.livonianKeyboardActive=!0,console.info("Livonian keyboard activated")}();)

If you don't see a link above, open this same page on [GitHub Pages](https://reinis-zumbergs.github.io/livonian-keyboard/bookmarklet/BOOKMARKLET.html).
