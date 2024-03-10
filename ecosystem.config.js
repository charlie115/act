module.exports = {
  apps : [{
    name: 'trade_core',
    script: 'trade_core_main.py',
    interpreter: 'python3.9',
    args: "-p 2",
    restart_delay: 3000,
    autorestart: false,
  },
  ],

  // deploy : {
  //   production : {
  //     user : 'SSH_USERNAME',
  //     host : 'SSH_HOSTMACHINE',
  //     ref  : 'origin/master',
  //     repo : 'GIT_REPOSITORY',
  //     path : 'DESTINATION_PATH',
  //     'pre-deploy-local': '',
  //     'post-deploy' : 'npm install && pm2 reload ecosystem.config.js --env production',
  //     'pre-setup': ''
  //   }
  // }
};
