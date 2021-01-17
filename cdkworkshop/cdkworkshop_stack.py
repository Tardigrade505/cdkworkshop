"""Stack definition for POC project."""

from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_cognito as cognito,
    core,
)


class CdkworkshopStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a VPC for Aurora (required for serverless Aurora)
        aurora_vpc = ec2.Vpc(self, 'AuroraVpc')

        # Create serverless MySQL Aurora cluster
        aurora_cluster = rds.ServerlessCluster(
            self,
            'AuroraCluster',
            vpc=aurora_vpc,
            engine=rds.DatabaseClusterEngine.AURORA_MYSQL,
            default_database_name='core'
        )

        # Handler for the hello endpoint
        hello_lambda = _lambda.Function(
            self, 'HelloHandler',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('lambda'),
            handler='hello.handler',
        )

        # Handler for the GET /user_accounts endpoint
        get_user_account_lambda = _lambda.Function(
            self, 'GetUserAccount',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('lambda'),
            handler='get_user_account.handler',
            environment={
                'CLUSTER_ARN': aurora_cluster.cluster_arn,
                'SECRET_ARN': aurora_cluster.secret.secret_arn,
                'DB_NAME': 'core',
            }
        )

        # Grant the lambda function the required permissions to access the database
        aurora_cluster.grant_data_api_access(get_user_account_lambda)  # This also enables the data api

        # Cognito User Pool for sign up and authorization
        user_pool = cognito.UserPool(
            self,
            'user-pool',
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True,
                phone=False
            ),
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True
            )
        )

        # User pool client - used for sign up and sign in and password recovery
        user_pool.add_client('app-client',
        auth_flows=cognito.AuthFlow(
            user_password=True,
            user_srp=True
        ))

        # Create the API Gateway REST API
        api = apigw.RestApi(self, 'test-api')

        # Create custom authorizer, modeled after work around detailed here:
        # https://github.com/aws/aws-cdk/issues/723#issuecomment-504753280
        cognito_authorizer = apigw.CfnAuthorizer(
            self,
            'CognitoAuthorizer',
            type='COGNITO_USER_POOLS',
            provider_arns=[user_pool.user_pool_arn],
            identity_source='method.request.header.Authorization',
            rest_api_id=api.rest_api_id,
            name='CognitoAuthorizer'
        )

        # Hello resource and endpoint, handled by the hello lambda
        hello_resource = api.root.add_resource('hello')
        hello_method = hello_resource.add_method(
            'GET',
            integration=apigw.LambdaIntegration(hello_lambda))
        hello_method_resource = hello_method.node.find_child('Resource')
        hello_method_resource.add_property_override('AuthorizationType', apigw.AuthorizationType.COGNITO)
        hello_method_resource.add_property_override( 'AuthorizerId', {"Ref": cognito_authorizer.logical_id})

        # Add user_account resource
        user_account_resource = api.root.add_resource('user_account')

        # Add GET handler for user_account
        get_user_account_method = user_account_resource.add_method(
            'GET', integration=apigw.LambdaIntegration(get_user_account_lambda))
        get_user_account_method_resource = get_user_account_method.node.find_child('Resource')
        get_user_account_method_resource.add_property_override('AuthorizationType', apigw.AuthorizationType.COGNITO)
        get_user_account_method_resource.add_property_override( 'AuthorizerId', {"Ref": cognito_authorizer.logical_id})
