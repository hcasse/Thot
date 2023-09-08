/* thot.tparser -- Thot document parser
  Copyright (C) 2009  <hugues.casse@laposte.net>

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.*/

var com_http = new XMLHttpRequest();

function com_download() {
	if(this.readyState == 4) {
		if(this.status == 200) {
			node = document.getElementById(this.id);
			node.innerHTML = this.responseText;
		}
		else
			console.log("failed downloading.");
	}
}

function com_show_last(id) {
	const cont = document.getElementById(id);
	const elt = cont.lastChild
	if(elt == null)
		return;
	const etop = elt.offsetTop;
	const ebot = etop + elt.clientHeight;
	const ctop = cont.scrollTop;
	const cbot = ctop + cont.clientHeight;
	if(etop < ctop)
		cont.scrollTop -= ctop - etop;
	else if(ebot > cbot)
		cont.scrollTop += ebot - cbot;
}

com_http.onreadystatechange = function() {
	if(this.readyState == 4) {
		if(this.status != 200) {
			console.error("HTTP error: " + this.status);
		}
		else {
			ans = JSON.parse(this.responseText);
			for(const a of ans) {
				switch(a["type"]) {
				case "call":
					var f = window[a["fun"]];
					f(a["args"]);
					break;
				case "set-style":
					component = document.getElementById(a["id"]);
					component.style[a["attr"]] = a["val"];
					break;
				case "add-class":
					component = document.getElementById(a["id"]);
					component.classList.add(a["class"]);
					break;
				case "set-attr":
					component = document.getElementById(a["id"]);
					component.setAttribute(a["attr"], a["val"]);
					break;
				case "remove-attr":
					component = document.getElementById(a["id"]);
					component.removeAttribute(a["attr"]);
					break;
				case 'set-content':
					component = document.getElementById(a["id"]);
					component.innerHTML = a["content"];
					break;
				case 'set-value':
					component = document.getElementById(a["id"]);
					component.value = a["val"];
					break;
				case 'remove-class':
					component = document.getElementById(a["id"]);
					component.classList.remove(a["class"]);
					break;
				case "download":
					req = new XMLHttpRequest();
					req.id = a["id"]
					req.onreadystatechange = com_download
					req.open("GET", a["path"], true);
					req.send();
					break;
				case "append":
					converter.innerHTML = a["content"]
					component = document.getElementById(a["id"]);
					for(const child of converter.children)
						component.append(child);
					while(converter.firstChild)
						converter.removeChild(converter.firstChild);
					break;
				case "clear":
					component = document.getElementById(a["id"]);
					while(component.firstChild)
						component.removeChild(component.firstChild);
					break;
				case "show-last":
					com_show_last(a["id"]);
					break;
				default:
					console.error("unknow command: " + a);
					break;
				}
			}
		}
	}
}

function com_post(obj) {
	com_messages.push(obj);
}

function com_send(target, obj) {
	com_http.open("POST", target, true);
	com_http.send(JSON.stringify(obj));
}
