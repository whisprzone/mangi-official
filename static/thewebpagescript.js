
function openNav() {
  document.getElementById("searchpanelid").style.width = "400px";
  document.getElementById("searchpanelid").style.borderRight = "4px solid #2b2b2b";
  document.getElementById("searchiconid").style.visibility = "visible";
}

function closeNav() {
  document.getElementById("searchpanelid").style.width = "0";
  document.getElementById("searchpanelid").style.borderRight = "0px solid #2b2b2b";
  document.getElementById("searchiconid").style.visibility = "hidden";
}
