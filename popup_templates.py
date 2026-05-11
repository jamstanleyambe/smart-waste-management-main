"""
Premium Popup Templates for Smart Waste Management Dashboard
"""

def _fill_bar(fill, bar_id):
    """Animated fill level progress bar + colour-coded badge."""
    if fill >= 85:
        bar_col = "#e74c3c"; badge_bg = "rgba(231,76,60,0.25)"; status = "CRITICAL"
    elif fill >= 65:
        bar_col = "#f39c12"; badge_bg = "rgba(243,156,18,0.25)"; status = "WARNING"
    else:
        bar_col = "#2ecc71"; badge_bg = "rgba(46,204,113,0.25)"; status = "GOOD"
    return f"""
<style>
@keyframes growBar{{from{{width:0%}}to{{width:{fill:.1f}%}}}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
</style>
<div style="background:{badge_bg};border:1px solid {bar_col};border-radius:8px;padding:8px 10px;margin:8px 0;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
    <span style="font-size:10px;font-weight:700;letter-spacing:1px;color:rgba(255,255,255,.6);">FILL LEVEL</span>
    <span id="{bar_id}" style="font-size:18px;font-weight:800;color:{bar_col};">{fill:.1f}%</span>
  </div>
  <div style="background:rgba(255,255,255,.15);border-radius:20px;height:8px;overflow:hidden;">
    <div id="{bar_id}-bar" style="height:100%;width:{fill:.1f}%;background:linear-gradient(90deg,{bar_col},{bar_col}cc);border-radius:20px;animation:growBar .8s ease-out;"></div>
  </div>
  <div style="text-align:right;font-size:9px;margin-top:3px;color:{bar_col};font-weight:600;">{status}</div>
</div>"""


def _composition_row(icon, label, pct, col):
    return f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
  <span style="font-size:12px;">{icon} {label}</span>
  <div style="display:flex;align-items:center;gap:6px;">
    <div style="width:60px;background:rgba(255,255,255,.12);border-radius:10px;height:5px;">
      <div style="width:{pct}%;height:100%;background:{col};border-radius:10px;"></div>
    </div>
    <span style="font-size:12px;font-weight:700;color:{col};min-width:36px;text-align:right;">{pct:.1f}%</span>
  </div>
</div>"""


def _refresh_btn(fn, label="🔄 Refresh Live Data"):
    return f"""
<button onclick="{fn}()" id="refresh-btn" style="
  width:100%;margin-top:10px;padding:10px;border:none;border-radius:10px;
  background:linear-gradient(135deg,#f1c40f,#e67e22);color:#1a1a2e;
  font-weight:800;font-size:13px;cursor:pointer;
  box-shadow:0 4px 15px rgba(241,196,15,.35);
  transition:transform .15s,box-shadow .15s;letter-spacing:.3px;"
  onmouseover="this.style.transform='scale(1.03)';this.style.boxShadow='0 6px 20px rgba(241,196,15,.5)'"
  onmouseout="this.style.transform='scale(1)';this.style.boxShadow='0 4px 15px rgba(241,196,15,.35)'"
>{label}</button>"""


def _hero_image(url, img_id):
    if not url:
        return ""
    return f"""
<div style="position:relative;border-radius:10px;overflow:hidden;margin:10px 0;box-shadow:0 4px 16px rgba(0,0,0,.4);">
  <img id="{img_id}" src="{url}"
       style="width:100%;height:130px;object-fit:cover;display:block;" alt="Bin camera"/>
  <div style="position:absolute;bottom:0;left:0;right:0;padding:6px 10px;
              background:linear-gradient(transparent,rgba(0,0,0,.7));
              font-size:9px;color:rgba(255,255,255,.8);letter-spacing:.8px;">
    📷 LATEST CAPTURE
  </div>
</div>"""


def bin_popup_html(b, is_searched=False):
    """Returns premium HTML for a bin map popup."""
    fill   = b['fill_level']
    img    = b.get('latest_image_url', '')
    bid    = b['bin_id']
    org    = b['organic_percentage']
    pla    = b['plastic_percentage']
    met    = b['metal_percentage']
    upd    = b.get('last_updated', '')[:16].replace('T', ' ')
    lat    = b['latitude']
    lon    = b['longitude']

    bar_id  = "star-fill"  if is_searched else "fill-level"
    img_id  = "star-image" if is_searched else "latest-image"
    upd_id  = "star-updated" if is_searched else "last-updated"
    fn_name = "updateStarData" if is_searched else "updateData"
    api_bid = bid

    # Header accent
    if is_searched:
        header_badge = '<div style="display:inline-block;background:linear-gradient(135deg,#f1c40f,#e67e22);color:#1a1a2e;padding:4px 14px;border-radius:20px;font-weight:800;font-size:11px;letter-spacing:.8px;margin-top:6px;box-shadow:0 2px 8px rgba(241,196,15,.4);">⭐ SEARCHED ITEM</div>'
        card_border  = "border:2px solid rgba(241,196,15,.6);"
        header_grad  = "background:linear-gradient(160deg,#0f2027,#203a43,#2c5364);"
    else:
        header_badge = ""
        card_border  = "border:1px solid rgba(255,255,255,.15);"
        header_grad  = "background:linear-gradient(160deg,#1a1a2e,#16213e,#0f3460);"

    hero    = _hero_image(img, img_id)
    bar     = _fill_bar(fill, bar_id)
    c_org   = _composition_row("🥬","Organic", org, "#2ecc71")
    c_pla   = _composition_row("♻️","Plastic",  pla, "#3498db")
    c_met   = _composition_row("🔩","Metal",    met, "#bdc3c7")
    btn     = _refresh_btn(fn_name)

    # JS fetch block
    js = f"""
<script>
function {fn_name}(){{
  var btn=document.getElementById('refresh-btn');
  btn.innerText='⏳ Loading...'; btn.disabled=true;
  fetch('http://localhost:8000/api/bin-data/?bin_id={api_bid}')
  .then(r=>r.json()).then(data=>{{
    var b=(data.results&&data.results.length>0)?data.results[0]:(data.length>0?data[0]:data);
    if(b&&b.fill_level!==undefined){{
      var f=parseFloat(b.fill_level);
      document.getElementById('{bar_id}').innerText=f.toFixed(1)+'%';
      var bar=document.getElementById('{bar_id}-bar');
      if(bar)bar.style.width=f.toFixed(1)+'%';
      if(b.last_updated)document.getElementById('{upd_id}').innerText=b.last_updated.substring(0,16).replace('T',' ');
      if(b.latest_image_url){{var im=document.getElementById('{img_id}');if(im){{im.src=b.latest_image_url;im.style.display='block';}}}}
    }}
    btn.innerText='✅ Updated!'; btn.disabled=false;
    setTimeout(()=>{{btn.innerText='🔄 Refresh Live Data';}},2000);
  }}).catch(()=>{{btn.innerText='❌ Error';btn.disabled=false;setTimeout(()=>{{btn.innerText='🔄 Refresh Live Data';}},2000);}});
}}
</script>"""

    return f"""
<div style="font-family:'Segoe UI',system-ui,sans-serif;{header_grad}color:#fff;
  border-radius:16px;overflow:hidden;{card_border}
  box-shadow:0 20px 60px rgba(0,0,0,.5);animation:fadeIn .4s ease-out;width:285px;">

  <!-- HEADER -->
  <div style="padding:14px 16px 10px;border-bottom:1px solid rgba(255,255,255,.1);text-align:center;">
    <div style="font-size:11px;letter-spacing:2px;color:rgba(255,255,255,.45);margin-bottom:4px;">SMART WASTE</div>
    <div style="font-size:17px;font-weight:800;letter-spacing:.5px;">🗑️ {bid}</div>
    {header_badge}
  </div>

  <!-- BODY -->
  <div style="padding:12px 14px;">
    {hero}
    {bar}

    <!-- COMPOSITION -->
    <div style="background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);
                border-radius:10px;padding:10px 12px;margin-top:8px;">
      <div style="font-size:10px;letter-spacing:1.5px;color:rgba(255,255,255,.45);margin-bottom:8px;">WASTE COMPOSITION</div>
      {c_org}{c_pla}{c_met}
    </div>

    <!-- COORDINATES -->
    <div style="display:flex;align-items:center;gap:6px;margin-top:8px;
                background:rgba(255,255,255,.04);border-radius:8px;padding:7px 10px;">
      <span style="font-size:11px;color:rgba(255,255,255,.5);">📍</span>
      <span style="font-size:10px;color:rgba(255,255,255,.55);">{lat:.4f}, {lon:.4f}</span>
    </div>

    {btn}

    <!-- FOOTER -->
    <div style="text-align:center;font-size:9px;color:rgba(255,255,255,.3);margin-top:8px;letter-spacing:.5px;">
      🕐 UPDATED <span id="{upd_id}">{upd}</span>
    </div>
  </div>
  {js}
</div>"""
