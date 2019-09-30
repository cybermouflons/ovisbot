def chunkify(text, limit):
    chunks = []
    while len(text) > limit: # Embed has a limit of 2048 chars 
        idx = text.index('\n',limit)
        chunks.append(text[:idx])
        text = text[idx:]
    chunks.append(text) 
    return chunks

def escape_md(text):
    return text.replace("_","\_").replace("*","\*").replace(">>>",'\>>>')