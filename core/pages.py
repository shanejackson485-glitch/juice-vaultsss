import io, os, platform, shutil, subprocess, sys, time, zipfile
from datetime import datetime
from pathlib import Path
import streamlit as st
from core.security import safe_path, sensitive, redact

def project(svc):
    return Path(svc.settings.get("project",Path.cwd())).expanduser().resolve()

def env_map(folder):
    result={}
    path=folder/".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8",errors="ignore").splitlines():
            line=line.strip()
            if line and not line.startswith("#") and "=" in line:
                k,v=line.split("=",1); result[k.strip()]=v.strip().strip('"').strip("'")
    return result

def launch(svc, command=None):
    folder=project(svc)
    ok,msg=svc.process.start(command or svc.settings.get("command"),folder,env_map(folder))
    (st.success if ok else st.error)(msg)

def log_view(svc, limit=1000):
    rows=svc.process.snapshot(limit)
    if not rows:
        st.info("No process output yet. Start your bot to populate the console.")
        return
    html=[]
    for row in rows:
        cls="log-error" if row["level"]=="ERROR" else "log-warn" if row["level"]=="WARN" else "log-info"
        html.append(f"<span class='{cls}'>[{row['time']}] [{row['level']}] {redact(row['message'])}</span>")
    st.markdown("<div class='logbox'>"+"<br>".join(html)+"</div>",unsafe_allow_html=True)

def overview(svc):
    st.title("Overview")
    state=svc.process.status(); folder=project(svc)
    elapsed=state["uptime"]; uptime=f"{elapsed//3600}h {(elapsed%3600)//60}m {elapsed%60}s" if state["running"] else "—"
    cols=st.columns(4)
    cols[0].metric("BOT STATUS","ONLINE" if state["running"] else "OFFLINE")
    cols[1].metric("PROCESS ID",state["pid"] or "—")
    cols[2].metric("UPTIME",uptime)
    cols[3].metric("LAST EXIT",state["exit_code"] if state["exit_code"] is not None else "—")
    st.markdown("### Process controls")
    a,b,c=st.columns(3)
    with a:
        if st.button("▶  START BOT",type="primary",use_container_width=True,disabled=state["running"]):
            launch(svc); st.rerun()
    with b:
        if st.button("↻  RESTART",use_container_width=True,disabled=not state["running"]):
            ok,msg=svc.process.restart(svc.settings.get("command"),folder,svc.settings.get("restart_delay",2),env_map(folder))
            (st.success if ok else st.error)(msg); st.rerun()
    with c:
        if st.button("■  STOP BOT",use_container_width=True,disabled=not state["running"]):
            ok,msg=svc.process.stop(); (st.success if ok else st.error)(msg); st.rerun()
    file_count,line_count=svc.diagnostics.code_stats(folder) if folder.is_dir() else (0,0)
    st.markdown("### Project snapshot")
    x,y,z=st.columns(3); x.metric("SOURCE FILES",file_count); y.metric("LINES OF CODE",f"{line_count:,}"); z.metric("WORKSPACE",folder.name or str(folder))
    st.markdown("### Recent activity"); log_view(svc,12)

def console(svc):
    st.title("Console")
    state=svc.process.status()
    a,b=st.columns([3,1]); a.write(f"**{'● RUNNING' if state['running'] else '○ STOPPED'}** · PID `{state['pid'] or '—'}`")
    if b.button("Clear console",use_container_width=True): svc.process.clear(); st.rerun()
    log_view(svc,6000)
    st.download_button("Download console log",svc.process.log_text(),"bot-console.log","text/plain")

def startup(svc):
    st.title("Startup")
    settings=svc.settings
    runtime=st.selectbox("Runtime",["Python","Node.js","Custom"],index=["Python","Node.js","Custom"].index(settings.get("runtime","Python")))
    entry=st.text_input("Entry file",settings.get("entry","bot.py"))
    suggestion=f"python {entry}" if runtime=="Python" else f"node {entry}" if runtime=="Node.js" else settings.get("command")
    command=st.text_input("Startup command",settings.get("command",suggestion))
    delay=st.slider("Restart delay",0,15,int(settings.get("restart_delay",2)))
    auto=st.toggle("Auto-restart after unexpected exit",settings.get("auto_restart",False))
    st.info("Commands are launched without a shell. Use an executable and arguments; pipes, redirects and shell operators are not supported.")
    if st.button("Save startup configuration",type="primary"):
        settings.set_many(runtime=runtime,entry=entry,command=command,restart_delay=delay,auto_restart=auto)
        st.success("Startup settings saved.")
    x,y=st.columns(2)
    with x:
        if st.button("Start with this command",disabled=svc.process.running,type="primary"):
            settings.set_many(command=command); launch(svc,command); st.rerun()
    with y:
        if st.button("Restart with this command",disabled=not svc.process.running):
            ok,msg=svc.process.restart(command,project(svc),delay,env_map(project(svc)))
            (st.success if ok else st.error)(msg); st.rerun()

def templates(svc):
    st.title("Templates")
    st.caption("Generate a starter project. Existing files are skipped by default.")
    items=svc.templates.all()
    chosen=st.selectbox("Template catalog",items,format_func=lambda t:t.name)
    st.markdown(f"<div class='card'><div class='eyebrow'>{chosen.language} STARTER</div><h3>{chosen.name}</h3><p class='muted'>{chosen.description}</p><b>Entry:</b> <code>{chosen.entry}</code><br><b>Command:</b> <code>{chosen.command}</code><br><br><b>Included files</b><br>{'<br>'.join('• '+f for f in chosen.files)}</div>",unsafe_allow_html=True)
    dest=st.text_input("Destination folder",str(project(svc)))
    overwrite=st.checkbox("Overwrite matching files",False)
    if st.button("Generate template",type="primary"):
        try:
            item,written,skipped=svc.templates.create(chosen.key,dest,overwrite)
            svc.settings.set_many(project=str(Path(dest).resolve()),command=item.command,runtime=item.language,entry=item.entry)
            st.success(f"Generated {len(written)} files; skipped {len(skipped)}.")
            if written: st.code("\\n".join("✓ "+x for x in written))
            if skipped: st.warning("Skipped existing files: "+", ".join(skipped))
        except Exception as exc: st.error(str(exc))

def files(svc):
    st.title("Files")
    root=project(svc)
    if not root.is_dir(): st.error("Project folder does not exist."); return
    st.caption(f"Workspace · `{root}`")
    relative=st.text_input("Folder (relative to project root)",".")
    try: folder=safe_path(root,relative)
    except ValueError as exc: st.error(str(exc)); return
    if not folder.is_dir(): st.error("Not a directory."); return
    for item in sorted(folder.iterdir(),key=lambda p:(not p.is_dir(),p.name.lower())):
        if item.name in {".git","node_modules",".venv","venv","__pycache__"}: continue
        st.markdown(f"<div class='file-row'>{'📁' if item.is_dir() else '📄'} &nbsp; <b>{item.name}</b> <span class='muted'>· {'folder' if item.is_dir() else str(item.stat().st_size)+' bytes'}</span></div>",unsafe_allow_html=True)
    st.divider(); st.markdown("### Editor")
    rel=st.text_input("File path to edit",key="edit_path")
    if rel:
        try:
            target=safe_path(root,rel)
            if not target.is_file(): st.info("Enter an existing file path.")
            elif sensitive(target.name): st.warning("Secret files are intentionally not displayed in the editor.")
            elif target.stat().st_size>1_000_000: st.warning("File is larger than 1 MB.")
            else:
                text=target.read_text(encoding="utf-8",errors="replace")
                edited=st.text_area("File contents",text,height=340)
                if st.button("Save changes"): target.write_text(edited,encoding="utf-8"); st.success("Saved.")
        except Exception as exc: st.error(str(exc))
    with st.expander("Create a file or folder"):
        with st.form("create_path"):
            name=st.text_input("Relative path (e.g. cogs/admin.py)")
            kind=st.selectbox("Type",["File","Folder"])
            body=st.text_area("Initial contents",disabled=kind=="Folder")
            go=st.form_submit_button("Create",type="primary")
            if go:
                try:
                    target=safe_path(root,name)
                    if target.exists(): st.error("Already exists.")
                    else:
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.mkdir() if kind=="Folder" else target.write_text(body,encoding="utf-8")
                        st.success("Created."); st.rerun()
                except Exception as exc: st.error(str(exc))
    with st.expander("Upload files"):
        uploads=st.file_uploader("Select files",accept_multiple_files=True)
        if uploads and st.button("Upload selected"):
            for upload in uploads:
                target=safe_path(folder,Path(upload.name).name)
                if not target.exists(): target.write_bytes(upload.getbuffer())
            st.success("Upload complete."); st.rerun()

def tools(svc):
    st.title("Tools")
    folder=project(svc)
    st.markdown("### Diagnostics")
    for check in svc.diagnostics.inspect(folder):
        st.markdown(f"<div class='file-row'><b>{'✓' if check['ok'] else '⚠'} {check['name']}</b><br><span class='muted'>{check['detail']}</span></div>",unsafe_allow_html=True)
    n,lines=svc.diagnostics.code_stats(folder) if folder.is_dir() else (0,0)
    st.metric("Lines of code",f"{lines:,}",f"{n} source files")
    st.divider(); st.markdown("### Dependency installer")
    choice=st.selectbox("Action",["Install requirements.txt","Install one Python package","Run npm install"])
    package=st.text_input("Package name",placeholder="discord.py")
    confirm=st.checkbox("I understand this runs a package manager in my project folder.")
    if st.button("Run package action",type="primary",disabled=not confirm):
        if choice=="Install requirements.txt": args=[sys.executable,"-m","pip","install","-r","requirements.txt"]
        elif choice=="Run npm install": args=["npm","install"]
        else: args=[sys.executable,"-m","pip","install",package.strip()]
        if choice!="Install one Python package" or package.strip():
            try:
                result=subprocess.run(args,cwd=folder,capture_output=True,text=True,timeout=300)
                st.code((result.stdout+"\\n"+result.stderr)[-14000:] or "No output")
                (st.success if result.returncode==0 else st.error)(f"Installer exit code: {result.returncode}")
            except Exception as exc: st.error(str(exc))
    st.divider(); st.markdown("### Runtime checks")
    a,b=st.columns(2)
    with a:
        if st.button("Python version"): st.code(sys.version)
    with b:
        if st.button("Node version"):
            node=shutil.which("node")
            if node:
                try: st.code(subprocess.check_output([node,"--version"],text=True,timeout=5))
                except Exception as exc: st.error(str(exc))
            else: st.warning("Node.js is not on PATH.")
    if st.button("List Python packages"):
        try: st.code(subprocess.check_output([sys.executable,"-m","pip","list"],text=True,timeout=30))
        except Exception as exc: st.error(str(exc))

def environment(svc):
    st.title("Environment")
    folder=project(svc); path=folder/".env"; values=env_map(folder)
    st.caption("Manage local environment variables. Existing values are never displayed.")
    if values:
        for key,value in values.items():
            st.markdown(f"<div class='file-row'><b>{key}</b><span class='muted'> · {'configured' if value else 'empty'} · hidden</span></div>",unsafe_allow_html=True)
    else: st.info("No .env file exists yet.")
    with st.form("env_add"):
        key=st.text_input("Variable name",placeholder="DISCORD_TOKEN")
        value=st.text_input("Variable value",type="password")
        save=st.form_submit_button("Save variable",type="primary")
        if save:
            if not key or not key.replace("_","").isalnum() or key[0].isdigit(): st.error("Invalid variable name.")
            elif "\\n" in value or "\\r" in value: st.error("Newlines are not allowed.")
            else:
                values[key]=value
                path.write_text("\\n".join(f"{k}={v}" for k,v in values.items())+"\\n",encoding="utf-8")
                try: os.chmod(path,0o600)
                except OSError: pass
                st.success(f"Saved {key}."); st.rerun()
    st.warning("Never commit .env to GitHub or share it. Keep .env listed in .gitignore.")

def backups(svc):
    st.title("Backups")
    folder=project(svc)
    st.caption("Build a downloadable ZIP of the current project.")
    exclusions=svc.settings.get("backup_excludes",[])
    st.write("Excluded folders:",", ".join(exclusions))
    name=st.text_input("Archive name",f"{folder.name}-{datetime.now():%Y%m%d-%H%M%S}.zip")
    if st.button("Build ZIP backup",type="primary"):
        try:
            buffer=io.BytesIO()
            with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as archive:
                for path in folder.rglob("*"):
                    if not path.is_file(): continue
                    rel=path.relative_to(folder)
                    if any(part in exclusions for part in rel.parts) or sensitive(path.name): continue
                    archive.write(path,rel.as_posix())
            st.session_state["backup_data"]=buffer.getvalue()
            st.session_state["backup_file"]=Path(name).name
            st.success("Backup ready. .env and excluded folders were omitted.")
        except Exception as exc: st.error(str(exc))
    if st.session_state.get("backup_data"):
        st.download_button("Download backup",st.session_state["backup_data"],st.session_state["backup_file"],"application/zip",type="primary")

def settings(svc):
    st.title("Settings")
    folder=st.text_input("Project directory",svc.settings.get("project"))
    delay=st.number_input("Default restart delay",0,15,int(svc.settings.get("restart_delay",2)))
    excludes=st.text_input("Backup exclusions",",".join(svc.settings.get("backup_excludes",[])))
    if st.button("Save settings",type="primary"):
        svc.settings.set_many(project=str(Path(folder).expanduser().resolve()),restart_delay=delay,backup_excludes=[x.strip() for x in excludes.split(",") if x.strip()])
        st.success("Settings saved.")
    st.markdown("### Runtime information")
    st.code(f"Platform: {platform.platform()}\\nPython: {sys.version}\\nStreamlit: {st.__version__}\\nDashboard: {Path.cwd()}")

def documentation(svc):
    st.title("Documentation")
    st.markdown("""
    ### Getting started
    1. Set your bot project folder in the sidebar.
    2. Use **Templates** to scaffold a project or **Files** to inspect one.
    3. Set the entry point and startup command in **Startup**.
    4. Add `DISCORD_TOKEN` in **Environment**.
    5. Start from **Overview** and inspect output in **Console**.

    ### Included templates
    - discord.py Prefix + Slash
    - discord.py Cogs Architecture
    - discord.js v14
    - Python Minimal

    ### Safety
    - Keep this dashboard on localhost.
    - `.env` values are hidden and excluded from ZIP backups.
    - The process manager runs commands without a shell, but the selected executable still runs with your operating-system permissions.
    - Back up your project with Git before using bulk template generation.
    """)

PAGES={"Overview":overview,"Console":console,"Startup":startup,"Templates":templates,
       "Files":files,"Tools":tools,"Environment":environment,"Backups":backups,
       "Settings":settings,"Documentation":documentation}
