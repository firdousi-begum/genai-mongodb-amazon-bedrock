def load_env(file_path=".env"):
    with open(file_path, 'r') as f:
        env = f.readlines()
    dic = {}
    for l in env:
        key, *val = l.strip('\n').split('=')
        dic[key] = '='.join(val)
    return dic