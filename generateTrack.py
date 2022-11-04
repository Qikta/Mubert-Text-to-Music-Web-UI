import numpy as np
from sentence_transformers import SentenceTransformer
import httpx
import json
import time
import datetime
import requests
import os
from dotenv import load_dotenv
from createToken import create_token
load_dotenv()
 
minilm = SentenceTransformer('all-MiniLM-L6-v2')
 
mubert_tags_string = 'run 60,piano,tribal,action,kids,neo-classic,run 130,pumped,jazz / funk,ethnic,dubtechno,reggae,acid jazz,liquidfunk,funk,witch house,tech house,underground,artists,mystical,disco,sensorium,r&amp;b,agender,psychedelic trance / psytrance,peaceful,run 140,piano,run 160,setting,meditation,christmas,ambient,horror,cinematic,electro house,idm,bass,minimal,underscore,drums,glitchy,beautiful,technology,tribal house,country pop,jazz &amp; funk,documentary,space,classical,valentines,chillstep,experimental,trap,new jack swing,drama,post-rock,tense,corporate,neutral,happy,analog,funky,spiritual,sberzvuk special,chill hop,dramatic,catchy,holidays,fitness 90,optimistic,orchestra,acid techno,energizing,romantic,minimal house,breaks,hyper pop,warm up,dreamy,dark,urban,microfunk,dub,nu disco,vogue,keys,hardcore,aggressive,indie,electro funk,beauty,relaxing,trance,pop,hiphop,soft,acoustic,chillrave / ethno-house,deep techno,angry,dance,fun,dubstep,tropical,latin pop,heroic,world music,inspirational,uplifting,atmosphere,art,epic,advertising,chillout,scary,spooky,slow ballad,saxophone,summer,erotic,jazzy,energy 100,kara mar,xmas,atmospheric,indie pop,hip-hop,yoga,reggaeton,lounge,travel,running,folk,chillrave &amp; ethno-house,detective,darkambient,chill,fantasy,minimal techno,special,night,tropical house,downtempo,lullaby,meditative,upbeat,glitch hop,fitness,neurofunk,sexual,indie rock,future pop,jazz,cyberpunk,melancholic,happy hardcore,family / kids,synths,electric guitar,comedy,psychedelic trance &amp; psytrance,edm,psychedelic rock,calm,zen,bells,podcast,melodic house,ethnic percussion,nature,heavy,bassline,indie dance,techno,drumnbass,synth pop,vaporwave,sad,8-bit,chillgressive,deep,orchestral,futuristic,hardtechno,nostalgic,big room,sci-fi,tutorial,joyful,pads,minimal 170,drill,ethnic 108,amusing,sleepy ambient,psychill,italo disco,lofi,house,acoustic guitar,bassline house,rock,k-pop,synthwave,deep house,electronica,gabber,nightlife,sport &amp; fitness,road trip,celebration,electro,disco house,electronic'
mubert_tags = np.array(mubert_tags_string.split(','))
mubert_tags_embeddings = minilm.encode(mubert_tags)

 
def get_track_by_tags(tags, pat, duration, maxit=20, autoplay=False, loop=False):
    if loop:
        mode = "loop"
    else:
        mode = "track"
    r = httpx.post('https://api-b2b.mubert.com/v2/RecordTrackTTM',
                   json={
                       "method": "RecordTrackTTM",
                       "params": {
                           "pat": pat,
                           "duration": duration,
                           "tags": tags,
                           "mode": mode
                       }
                   })
 
    rdata = json.loads(r.text)
    assert rdata['status'] == 1, rdata['error']['text']
    trackurl = rdata['data']['tasks'][0]['download_link']
 
    print('Generating track ', end='')
    for i in range(maxit):
        r = httpx.get(trackurl)
        if r.status_code == 200:
            save_file(trackurl, tags)
            break
        time.sleep(1)
        print('.', end='')
    
    return trackurl
 
 
def find_similar(em, embeddings, method='cosine'):
    scores = []
    for ref in embeddings:
        if method == 'cosine':
            scores.append(1 - np.dot(ref, em) / (np.linalg.norm(ref) * np.linalg.norm(em)))
        if method == 'norm':
            scores.append(np.linalg.norm(ref - em))
    return np.array(scores), np.argsort(scores)
 
 
def get_tags_for_prompts(prompts, top_n=3, debug=False):
    prompts_embeddings = minilm.encode(prompts)
    ret = []
    for i, pe in enumerate(prompts_embeddings):
        scores, idxs = find_similar(pe, mubert_tags_embeddings)
        top_tags = mubert_tags[idxs[:top_n]]
        top_prob = 1 - scores[idxs[:top_n]]
        if debug:
            print(f"Prompt: {prompts[i]}\nTags: {', '.join(top_tags)}\nScores: {top_prob}\n\n\n")
        ret.append((prompts[i], list(top_tags)))
    return ret
 
 
 
def generate_track_by_prompt(email, prompt, duration, loop):
    load_dotenv()
    # 環境変数を参照
    pat = os.getenv('API_ACCESS_TOKEN')
    new_pat = create_token(email) if pat == None else pat

    print("prompt: ", prompt)
    print("duration: ", duration)
    print("loop: ", loop)
    _, tags = get_tags_for_prompts([prompt, ])[0]
    try:
        return get_track_by_tags(tags, new_pat, duration, autoplay=True, loop=loop)
    except Exception as e:
        print(str(e))
    print('\n')
 
 
def save_file(url, tags):
    if not os.path.exists("outputs"):
        os.mkdir("outputs")
    
    file_name = "outputs/" +get_file_name(tags) + ".mp3"
    url_data = requests.get(url).content
 
    with open(file_name, mode='wb') as f:
        f.write(url_data)
 
 
def get_file_name(tags):
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    d = now.strftime('%Y%m%d%H%M%S')

    tagname = ''
    if len(tags) > 0:
        for i in tags:
            tagname = tagname + i + '-'
 
    return tagname + d
 