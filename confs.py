import toml

def get_conf(conf_file):
    with open(conf_file, 'r',encoding='utf-8') as f:
        conf = toml.load(f)
    return conf

# 读取conf.toml配置文件
confg = get_conf('conf.toml')
print(confg)