'''
Download asset from GitHub release page
'''

import hashlib
import json
import os
import os.path
import re
import urllib.request

_DOWNLOAD_CACHE_DIR = '.onsdriver-cache'

def _gh_urlopen(url):
    req = urllib.request.Request(url)
    if 'GITHUB_TOKEN' in os.environ:
        token = os.environ['GITHUB_TOKEN']
        req.add_header('authorization', f'Bearer {token}')
    return urllib.request.urlopen(req)

def _get_release_url(repo_name):
    m = re.match(r'https?://github.com/([^/]+/[^/]+)/releases/(tags/[^/]+)/?$', repo_name)
    if m:
        return f'https://api.github.com/repos/{m[1]}/releases/{m[2]}'
    m = re.match(r'https?://github.com/([^/]+/[^/]+)(|/|/releases/?)$', repo_name)
    if m:
        return f'https://api.github.com/repos/{m[1]}/releases/latest'
    raise ValueError(f'Cannot get GitHub.com API URL for {repo_name}')

def _select_asset_from_gh(repo_name, file_re):
    if isinstance(file_re, str):
        file_re = re.compile(file_re)

    release_url = _get_release_url(repo_name)

    try:
        with _gh_urlopen(release_url) as res:
            latest = json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        # pylint: disable=raise-missing-from
        raise ValueError(f'{e}: {release_url}')

    aa = []
    for a in latest['assets']:
        name = a['name']
        if file_re.match(name):
            aa.append(a)
    if not aa:
        names = [a["name"] for a in latest["assets"]]
        raise ValueError(f'No matching assets, available {" ".join(names)}')

    aa = sorted(aa, key=lambda a: a['name'])

    if len(aa) > 1:
        print('Info: Multiple candidates:\n ' + '\n '.join([a['name'] for a in aa]))

    return aa[-1]

def _download_gh_asset(asset, force_download=False):
    name = asset['name']
    url = asset['browser_download_url']

    if asset['digest'] and asset['digest'].startswith('sha256:'):
        content_digest = asset['digest'][7:]
        path = f'{_DOWNLOAD_CACHE_DIR}/{content_digest}/{name}'
    else:
        content_digest = None
        url_digest = hashlib.sha256(url.encode()).hexdigest()
        path = f'{_DOWNLOAD_CACHE_DIR}/{url_digest}/{name}'

    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path) or force_download:
        with _gh_urlopen(url) as res:
            with open(path, 'wb') as fw:
                while True:
                    data = res.read(8192)
                    if not data:
                        break
                    fw.write(data)

    if content_digest:
        with open(path, 'rb') as fr:
            digest = hashlib.file_digest(fr, 'sha256')
        if content_digest == digest.hexdigest():
            return path

        if not force_download:
            return _download_gh_asset(asset, force_download=True)

        actual = digest.hexdigest()
        raise ValueError(f'{path}: Digest mismatch, expect {content_digest} got {actual}')

    # No content_digest, check the size only.
    cached_size = os.path.getsize(path)
    if asset['size'] == cached_size:
        return path

    if not force_download:
        return _download_gh_asset(asset, force_download=True)

    raise ValueError(f'{path}: size mismatch, expect {asset['size']} got {cached_size}')

def download_asset_with_file_re(repo_name, file_re):
    '''Download an asset from GitHub release page
    :param repo_name:  Repository URL like "https://github.com/owner/repo"
    :param file_re:    regex to select file to be downloaded
    '''
    asset = _select_asset_from_gh(repo_name, file_re)
    return _download_gh_asset(asset)
