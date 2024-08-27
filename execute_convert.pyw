import re

class McCmdSyntaxError(Exception):
    pass

def _execute_split(cmd: str) -> dict:
    """
    拆分execute命令参数
    """
    ret = {
        "selector": "",
        "position": "",
        "if_block": None,
        "sub_command": "",
    }
    exe = r"execute|/execute"
    res = re.match(exe,cmd)
    if res is None:
        raise McCmdSyntaxError
    cmd = cmd[res.end():].strip()
    
    selector = r'@\w[\s]*(\[(([^\[\]])|("([^"]*)")|(\[[^\[\]]*\]))*\])?'
    res = re.match(selector,cmd)
    if res is None:
        raise McCmdSyntaxError
    ret["selector"] = res.group()
    cmd = cmd[res.end():].strip()
    
    pos = r"[\s]*([~^][\-\.\d]*|[\d]*)" * 3
    res = re.match(pos,cmd)
    if res is None:
        raise McCmdSyntaxError
    ret["position"] = res.group()
    if re.match(r"((~[\s]*)|(^[\s]*))"*3 + r"$",ret["position"]) is not None:
        ret["position"] = None
    cmd = cmd[res.end():].strip()
    
    if (res := re.match("detect",cmd)) is None:
        ret["sub_command"] = cmd
        return ret
    cmd = cmd[res.end():].strip()
    if (res := re.match(pos,cmd)) is None:
        raise McCmdSyntaxError

    pos = res.group()
    cmd = cmd[res.end():].strip()
    if (block := re.match(r"[\S.*]*",cmd)) is None: raise McCmdSyntaxError
    cmd = cmd[block.end():].strip()
    block = block.group()
    
    if (data := re.match(r"[-\d]*",cmd)) is None: raise McCmdSyntaxError
    ret["sub_command"] = cmd[data.end():].strip()
    data = data.group()
    try:
        if int(data) < 0:
            data = ""
    except:
        raise McCmdSyntaxError  

    block = {
        "position":pos,
        "block":block,
        "data":data,
    }

    ret["if_block"] = block
    return ret

    
def execute_convert(cmd: str, optimize: bool = False) -> str:
    """
    只进行命令转换，不检查除execute语法，支持execute嵌套并进行简单优化
    Exception:  McCmdSyntaxError
    """
    if not cmd: return ""
    if cmd[0] == '/':start = '/'
    else: start = ''
    ret = ""
    while True:
        cmd_args = _execute_split(cmd)
        nexe_is_execute = (re.match(r"execute|/execute",cmd_args['sub_command']) is not None)
        if not optimize:
            ret += f"as {cmd_args["selector"]} at @s "

        elif nexe_is_execute:
            if not _execute_split(cmd_args["sub_command"])["selector"].find("@s") == -1:
                ret += f"as {cmd_args["selector"]} "
            # 旧版execute嵌套中，执行者不需要更改为前面execute的执行者，因为最终执行者在最后
            # 前面的execute应该只起到类似"at"的效果 (总之前面可以只使用"at",除非下一个execute的选择器是"@s")
            else:
                ret += f"at {cmd_args["selector"]} "
        else:
            # 这里⌈可能⌋需要修改执行者(as)&执行位置等(at), 目前无法判断
            if cmd_args["selector"].find("@s") != -1:
                ret += "at @s "
            else:
                ret += f"as {cmd_args["selector"]} at @s "

        if cmd_args["position"] is not None:
            ret += f"positioned {cmd_args['position']} "

        if cmd_args["if_block"] is not None:
            ret += f"if block {cmd_args['if_block']["position"]} {cmd_args['if_block']['block']} "+\
                    (f"{cmd_args['if_block']['data']} " if cmd_args['if_block']['data'] else "")
        
        if not nexe_is_execute:
            return start + "execute " + ret + "run " + cmd_args["sub_command"]
        
        cmd = cmd_args["sub_command"]
        
    
if __name__ == "__main__":
    #GUI
    import tkinter as tk
    from tkinter import scrolledtext
    from tkinter import messagebox
    class Execute_Shell:
        def __init__(self) -> None:
            self.root = tk.Tk()
            self.root.title("我的世界execute转换器")
            self.root.geometry("700x600+100+100")
            self._show_menu()

            tk.Label(self.root,text="旧execute",font=("微软雅黑",18),width=10,height=1).place(x=0,y=4) 
            self.cmd_input = scrolledtext.ScrolledText(self.root,font=("微软雅黑",18),width = 40,height = 7)
            self.cmd_input.place(x=10,y=40)
            tk.Button(self.root,text="生成指令",font=("微软雅黑",18),width=10,height=2,command=self._show_cmd).place(x=100,y=300)
            self.optimize = tk.BooleanVar(value=False)
            tk.Checkbutton(self.root,font=("微软雅黑",18),width=15,height=3,text="优化as/at\n(可能有bug)"
                           ,variable=self.optimize,onvalue=True,offvalue=False).place(x=300,y=300)
            self.root.mainloop()
            
            
        def _show_menu(self):
            self.topMenu = tk.Menu(self.root)
            self.topMenu.add_command(label="生成指令",command=self._show_cmd)
            self.root.config(menu=self.topMenu)
        def _show_cmd(self):
            try:
                self._show.destroy()
            except AttributeError:
                pass
            try:
                info = execute_convert(self.cmd_input.get(1.0,"end"),self.optimize.get())
            except:
                messagebox.showerror("execute转换器","execute指令格式错误!")
                return
            self._show = tk.Toplevel(self.root)
            self._show.title("生成结果")
            self._show.geometry("250x250+200+200")
            txt = scrolledtext.ScrolledText(self._show,font=("微软雅黑",20))
            
            txt.insert(tk.INSERT,info)
            txt.pack(fill=tk.BOTH)
    
    Execute_Shell()
