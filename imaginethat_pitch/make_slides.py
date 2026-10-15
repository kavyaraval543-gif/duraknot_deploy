from PIL import Image, ImageDraw, ImageFont
W,H=1920,1080
F="/usr/share/fonts/opentype/inter/"
def f(n,s): return ImageFont.truetype(F+n,s)
BG=(250,248,243); INK=(22,30,45); MUT=(95,105,120); BLUE=(28,78,157); ORANGE=(232,106,40); GREEN=(34,139,84); LINE=(225,221,212)
def base(num,tag):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,10],fill=BLUE); d.rectangle([0,0,W*num//8,10],fill=ORANGE)
    d.text((120,80),tag.upper(),font=f("Inter-SemiBold.otf",28),fill=ORANGE)
    d.text((120,H-80),"PULSE  ·  #ImagineThat Idea Pitch",font=f("Inter-Medium.otf",24),fill=MUT)
    d.text((W-120,H-80),f"{num:02d} / 08",font=f("Inter-Medium.otf",24),fill=MUT,anchor="ra")
    return im,d
def wrap(d,text,font,maxw):
    lines=[];cur=""
    for w in text.split():
        t=(cur+" "+w).strip()
        if d.textlength(t,font=font)<=maxw: cur=t
        else: lines.append(cur);cur=w
    lines.append(cur);return lines
def para(d,xy,text,font,fill,maxw,gap=1.35):
    x,y=xy
    for l in wrap(d,text,font,maxw):
        d.text((x,y),l,font=font,fill=fill); y+=int(font.size*gap)
    return y
def card(d,box,fill=(255,255,255)):
    d.rounded_rectangle(box,radius=28,fill=fill,outline=LINE,width=2)
S=[]
# 1 title
im,d=base(1,"Tata Imagination Challenge 2026")
d.text((120,300),"Pulse",font=f("InterDisplay-Bold.otf",220),fill=INK)
d.ellipse([720,370,780,430],fill=ORANGE)
para(d,(120,580),"A plug-in brain for every small factory machine in India.",f("Inter-Medium.otf",56),MUT,1100)
pts=[(1200,640),(1330,640),(1380,520),(1440,780),(1500,600),(1550,640),(1800,640)]
d.line(pts,fill=ORANGE,width=12,joint="curve")
d.text((120,820),"Kavya Raval",font=f("Inter-SemiBold.otf",36),fill=INK)
S.append(im)
# 2 hook
im,d=base(2,"The question")
para(d,(120,260),"“How much did this machine produce today — and why did it stop?”",f("InterDisplay-Bold.otf",96),INK,1600,1.2)
para(d,(120,640),"Most small-factory owners can't answer. Not because they don't care — because the data doesn't exist.",f("Inter-Medium.otf",48),MUT,1500)
S.append(im)
# 3 problem
im,d=base(3,"The problem")
d.text((120,200),"60M+",font=f("InterDisplay-Bold.otf",200),fill=BLUE)
d.text((120,430),"MSMEs in India — running on paper registers and guesswork",font=f("Inter-Medium.otf",44),fill=INK)
items=[("Idle time","Machines wait, nobody logs it"),("Micro-stoppages","2-minute halts add up to hours"),("Silent defects","Found at dispatch, not at source")]
for i,(a,b) in enumerate(items):
    x=120+i*570; card(d,[x,560,x+520,860])
    d.ellipse([x+40,600,x+80,640],fill=ORANGE)
    d.text((x+40,670),a,font=f("Inter-Bold.otf",44),fill=INK)
    para(d,(x+40,740),b,f("Inter-Regular.otf",32) if False else f("Inter-Medium.otf",32),MUT,440)
d.text((120,920),"Industrial monitoring software exists — but it's priced for big plants.",font=f("Inter-SemiBold.otf",34),fill=ORANGE)
S.append(im)
# 4 idea
im,d=base(4,"The idea")
d.text((120,200),"Clip on. Plug in. See everything.",font=f("InterDisplay-Bold.otf",88),fill=INK)
para(d,(120,340),"A low-cost sensor kit that retrofits onto any existing machine — no rewiring, no new machinery.",f("Inter-Medium.otf",42),MUT,1650)
blocks=[("Rotary encoder","Counts output & speed",BLUE),("Vibration sensor","Flags defect patterns",ORANGE),("ESP32 module","Streams data every second",GREEN)]
for i,(a,b,c) in enumerate(blocks):
    x=120+i*570; card(d,[x,520,x+520,860])
    d.rounded_rectangle([x+40,560,x+130,650],radius=18,fill=c)
    d.text((x+40,690),a,font=f("Inter-Bold.otf",44),fill=INK)
    d.text((x+40,760),b,font=f("Inter-Medium.otf",32),fill=MUT)
d.text((120,920),"Target cost: less than a smartphone.",font=f("Inter-SemiBold.otf",36),fill=ORANGE)
S.append(im)
# 5 how
im,d=base(5,"How it works")
d.text((120,200),"From machine to phone,\nevery second.",font=f("InterDisplay-Bold.otf",80),fill=INK,spacing=16)
steps=["Sensor reads the machine","Live dashboard computes OEE","Plain-language alerts"]
for i,s in enumerate(steps):
    y=480+i*130
    d.ellipse([120,y,190,y+70],fill=BLUE); d.text((155,y+35),str(i+1),font=f("Inter-Bold.otf",36),fill="white",anchor="mm")
    d.text((220,y+12),s,font=f("Inter-SemiBold.otf",42),fill=INK)
# phone
d.rounded_rectangle([1220,150,1700,960],radius=60,fill=(255,255,255),outline=INK,width=6)
d.text((1270,220),"Line 2 · Live",font=f("Inter-SemiBold.otf",30),fill=MUT)
d.text((1270,270),"OEE 78%",font=f("InterDisplay-Bold.otf",80),fill=INK)
for i,(lab,v,c) in enumerate([("Availability",.91,BLUE),("Performance",.88,GREEN),("Quality",.97,ORANGE)]):
    y=410+i*90
    d.text((1270,y),lab,font=f("Inter-Medium.otf",26),fill=MUT)
    d.rounded_rectangle([1270,y+38,1650,y+56],radius=9,fill=LINE); d.rounded_rectangle([1270,y+38,1270+int(380*v),y+56],radius=9,fill=c)
d.rounded_rectangle([1260,720,1660,900],radius=24,fill=(255,240,230),outline=ORANGE,width=3)
d.text((1290,745),"⚠ ALERT",font=f("Inter-Bold.otf",28),fill=ORANGE)
para(d,(1290,790),"Line 2 has been idle for 9 minutes.",f("Inter-SemiBold.otf",30),INK,340)
S.append(im)
# 6 proof
im,d=base(6,"Already built")
d.text((120,200),"Not just a slide.",font=f("InterDisplay-Bold.otf",96),fill=INK)
para(d,(120,340),"A working prototype, built for a real wire-fence manufacturer (Duraknot).",f("Inter-Medium.otf",42),MUT,1650)
pr=[("Firmware","ESP32 sketch streaming JSON at 1 Hz"),("Backend","Flask REST API, SQLite, alert engine"),("Dashboard","Live OEE, deployed online, runs offline too"),("Tested","Unit tests + benchmark-calibrated simulator")]
for i,(a,b) in enumerate(pr):
    x=120+(i%2)*850; y=470+(i//2)*220; card(d,[x,y,x+800,y+190])
    d.text((x+40,y+35),"✓  "+a,font=f("Inter-Bold.otf",42),fill=GREEN)
    d.text((x+40,y+110),b,font=f("Inter-Medium.otf",32),fill=INK)
d.text((120,940),"duraknotdashboard.vercel.app",font=f("Inter-SemiBold.otf",32),fill=BLUE)
S.append(im)
# 7 impact
im,d=base(7,"Why it matters")
d.text((120,200),"+5%",font=f("InterDisplay-Bold.otf",220),fill=GREEN)
para(d,(120,460),"utilisation gain — more output from the machines a factory already owns.",f("Inter-Medium.otf",46),INK,1100)
imp=[("More income","for owners"),("More jobs","as small units grow"),("Less waste","of material & energy")]
for i,(a,b) in enumerate(imp):
    y=300+i*190; card(d,[1300,y,1800,y+160])
    d.text((1340,y+30),a,font=f("Inter-Bold.otf",44),fill=INK); d.text((1340,y+92),b,font=f("Inter-Medium.otf",30),fill=MUT)
d.text((120,900),"Multiply across millions of MSMEs → a stronger backbone for India's economy.",font=f("Inter-SemiBold.otf",36),fill=ORANGE)
S.append(im)
# 8 close
im,d=base(8,"The vision")
para(d,(120,280),"When every machine has a pulse, every maker can grow.",f("InterDisplay-Bold.otf",110),INK,1650,1.15)
d.line([(120,720),(700,720),(760,620),(830,820),(890,680),(940,720),(1800,720)],fill=ORANGE,width=12,joint="curve")
d.text((120,830),"Thank you  ·  Kavya Raval",font=f("Inter-SemiBold.otf",44),fill=BLUE)
S.append(im)
for i,im in enumerate(S): im.save(f"slides/slide_{i+1}.png")
S[0].save("Pulse_ImagineThat_Slides.pdf",save_all=True,append_images=S[1:],resolution=150)
