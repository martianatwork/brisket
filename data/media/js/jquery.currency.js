/* Copyright (c) 2009 Michael Manning (actingthemaggot.com) Dual licensed under the MIT (MIT-LICENSE.txt) and GPL (GPL-LICENSE.txt) licenses.*/
(function(A){A.fn.extend({currency:function(B){var C={s:",",d:".",c:2};C=A.extend({},C,B);return this.each(function(){var D=(C.n||A(this).text());D=(typeof D==="number")?D:((/\./.test(D))?parseFloat(D):parseInt(D)),s=D<0?"-":"",i=parseInt(D=Math.abs(+D||0).toFixed(C.c))+"",j=(j=i.length)>3?j%3:0;A(this).text(s+(j?i.substr(0,j)+C.s:"")+i.substr(j).replace(/(\d{3})(?=\d)/g,"$1"+C.s)+(C.c?C.d+Math.abs(D-i).toFixed(C.c).slice(2):""));return this})}})})(jQuery);jQuery.currency=function(){var A=jQuery("<span>").text(arguments[0]).currency(arguments[1]);return A.text()};