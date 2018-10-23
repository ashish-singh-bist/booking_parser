<?php
namespace Deployer;

require 'recipe/common.php';

// Project name
set('application_name', 'Booking Scrapers');

set('ssh_type', 'native');
set('ssh_multiplexing', true);

// Project repository
set('repository', 'git@github.com:ashish-singh-bist/booking_scrapers.git');

set('shared_files', ['proxies.txt','modules/Config.py']);
set('shared_dirs', []);
set('writable_dirs', []);
set('allow_anonymous_stats', false);

set('keep_releases', 1);
set('git_tty', false);
set('default_stage', 'production');

// Hosts
inventory('hosts.yml');

desc('Deploy MV project');
task('deploy', [
    'deploy:prepare',
    'deploy:lock',
    'deploy:release',
    'deploy:update_code',
    'deploy:shared',
    'deploy:writable',
    'deploy:clear_paths',
    'deploy:symlink',
    'deploy:unlock',
    'cleanup',
    'success'
]);

// [Optional] if deploy fails automatically unlock.
after('deploy:failed', 'deploy:unlock');