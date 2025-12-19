'''
Download asset from GitHub release page
'''

import hashlib
import json
import os
import os.path
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from packaging.specifiers import SpecifierSet
from onsdriver import util

_DOWNLOAD_CACHE_DIR = '.onsdriver-cache'

def _gh_urlopen(url, params=None):
    if params:
        url = url + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    if 'GITHUB_TOKEN' in os.environ:
        token = os.environ['GITHUB_TOKEN']
        req.add_header('authorization', f'Bearer {token}')
    return urllib.request.urlopen(req)

def _get_release_url(repo_name):
    m = re.match(
            r'https?://(github.com|api.github.com/repos)/([^/]+/[^/]+)/releases/(tags/[^/]+)/?$',
            repo_name)
    if m:
        return f'https://api.github.com/repos/{m[2]}/releases/{m[3]}'
    m = re.match(
            r'https?://(github.com|api.github.com/repos)/([^/]+/[^/]+)(|/|/releases/?)$', repo_name)
    if m:
        return f'https://api.github.com/repos/{m[2]}/releases/latest'
    raise ValueError(f'Cannot get GitHub.com API URL for {repo_name}')

def _get_releases_url(repo_name):
    m = re.match(
            r'https?://(github.com|api.github.com/repos)/([^/]+/[^/]+)(|/|/releases/?)$', repo_name)
    if m:
        return f'https://api.github.com/repos/{m[2]}/releases'
    raise ValueError(f'Cannot get GitHub.com API URL for {repo_name}')

def _select_asset_from_gh(repo_name, file_re, filter_cb=None, version_specs=None):
    if isinstance(file_re, str):
        file_re = re.compile(file_re)

    if version_specs:
        release_url = _latest_release_with_version(repo_name, version_specs)
    else:
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
    if filter_cb:
        aa = filter_cb(aa)

    if len(aa) > 1:
        sys.stderr.write('Info: Multiple candidates:\n ' +
                         '\n '.join([a["name"] for a in aa]) + '\n')

    return aa[-1], latest

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
    util.ignore_directory(_DOWNLOAD_CACHE_DIR)

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

    raise ValueError(f'{path}: size mismatch, expect {asset["size"]} got {cached_size}')

def _list_releases(repo_name, include_prerelease=False):
    '''Get the list of releases
    :param repo_name:  Repository URL like "https://github.com/owner/repo"
    :param include_prerelease:
                       If false, exclude prerelease
    :return:           List of the release information
    '''
    releases_url = _get_releases_url(repo_name)
    page = 0
    while True:
        page += 1
        try:
            with _gh_urlopen(releases_url, params={'per_page': 100, 'page': page}) as res:
                releases = json.loads(res.read().decode())
        except urllib.error.HTTPError as e:
            if e.code==422: # Unprocessable Entity
                return
            raise ValueError(f'{e}: {releases_url}') from e

        if not releases:
            break

        if not include_prerelease:
            releases = [rel for rel in releases if not rel['prerelease']]

        yield from releases

def _latest_release_with_version(repo_name, version_specs):
    if isinstance(version_specs, str):
        version_specs = SpecifierSet(version_specs)
    for rel in _list_releases(repo_name):
        if version_specs.contains(rel['tag_name']):
            return rel['url']
    raise ValueError(f'No tags matching {version_specs} in {repo_name}')

def download_asset_with_file_re(
        repo_name, file_re, filter_cb=None, info_only=False, version_specs=None):
    '''Download an asset from GitHub release page
    :param repo_name:  Repository URL like "https://github.com/owner/repo" or a release URL
    :param file_re:    regex to select file to be downloaded
    :param filter_cb:  Callback function to filter assets
    :param version_specs:  Optional condition for version selection
    '''
    asset, release = _select_asset_from_gh(
            repo_name, file_re, filter_cb=filter_cb, version_specs=version_specs)
    if info_only:
        ret = {
                'name': asset['name'],
                'url': asset['browser_download_url'],
                'tag_name': release['tag_name'],
        }
        if asset['digest'] and asset['digest'].startswith('sha256:'):
            ret['digest'] = asset['digest'][7:]
        else:
            ret['size'] = asset['size']
        return json.dumps(ret, sort_keys=True)
    return _download_gh_asset(asset)


def _get_args():
    import argparse # pylint: disable=import-outside-toplevel
    parser = argparse.ArgumentParser()
    parser.add_argument('--release-url', action='store_true', default=False)
    parser.add_argument('--list-releases', action='store_true', default=False)
    parser.add_argument('repo', default=None)
    args = parser.parse_args()
    return args

def main():
    'Entry point'
    args = _get_args()

    if args.release_url:
        print(_get_release_url(args.repo))
        return

    if args.list_releases:
        for rel in _list_releases(args.repo):
            print(rel)

if __name__ == '__main__':
    main()
