import os
import collections
import json
import ftplib
from datetime import datetime
from urllib.request import urlretrieve

host = 'ftp.ncbi.nih.gov'
ftp_root = 'ftp://{}/'.format(host)

def ncbi_ftp_download(ftp_paths, directory):
    """
    Download files from the NCBI FTP server. Returns a dictionary with datetime
    information.
    """
    for ftp_path in ftp_paths:
        url = ftp_root + ftp_path
        path = os.path.join(directory, ftp_path.split('/')[-1])
        urlretrieve(url, path)

    versions = collections.OrderedDict()
    versions['retrieved'] = datetime.utcnow().isoformat()

    with ftplib.FTP(host) as ftp:
        ftp.login()
        for ftp_path in ftp_paths:
            modified = ftp.sendcmd('MDTM ' + ftp_path)
            _, modified = modified.split(' ')
            modified = datetime.strptime(modified, '%Y%m%d%H%M%S')
            versions[ftp_path] = modified.isoformat()
    
    return versions

if __name__ == '__main__':
    # Where to download files
    directory = 'download'
    
    # Specific files to download
    ftp_paths = [
        'gene/DATA/gene_history.gz',
        'gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz',
    ]
    versions = ncbi_ftp_download(ftp_paths, directory)
    
    # Save version info as JSON
    path = os.path.join('download', 'versions.json')
    with open(path, 'w') as write_file:
        json.dump(versions, write_file, indent=2)