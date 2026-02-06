# Infrastructure

CDK TypeScript infrastructure-as-code project for the workshop.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Build the project:
```bash
npm run build
```

3. Deploy the stack:
```bash
cdk deploy
```

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template