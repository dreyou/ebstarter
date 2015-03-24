#EB Utils
import subprocess
import json
import logging
import sys
import unittest
from mock import Mock

CMD_ENVS = "elastic-beanstalk-describe-environments -j"
CMD_APPS = "elastic-beanstalk-describe-applications -j"
CMD_REBUILD = "elastic-beanstalk-rebuild-environment -j"
CMD_DELETE = "elastic-beanstalk-delete-application -j -f"

CMD_CREATE_APP = "elastic-beanstalk-create-application-version -j -c"
#elastic-beanstalk-create-application-version -j -c -l samplepdfapp.Docker -a samplepdfapp -s dreyou.docker/samplepdf/Dockerfile
#{"CreateApplicationVersionResponse":{"CreateApplicationVersionResult":{"ApplicationVersion":{"ApplicationName":"samplepdfapp","DateCreated":1.427205143742E9,"DateUpdated":1.427205143742E9,"Description":null,"SourceBundle":{"S3Bucket":"dreyou.docker","S3Key":"samplepdf/Dockerfile"},"VersionLabel":"samplepdfapp.Docker"}},"ResponseMetadata":{"RequestId":"d52bb9d7-5b57-4903-b32d-f349b9247fd1"}}}

#AbortableOperationInProgress | Alerts | ApplicationName | CNAME                                 | DateCreated                    | DateUpdated                    | Description | EndpointURL    | EnvironmentId | EnvironmentName  | Health | HealthStatus | SolutionStackName                                      | Status | TemplateName | Tier                   | VersionLabel
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#false                        |        | samplepdfapp    | samplepdfapp-env.elasticbeanstalk.com | Sat Mar 21 22:58:43 +0300 2015 | Mon Mar 23 16:25:21 +0300 2015 | N/A         | 107.20.239.203 | e-krxppb6mw6  | samplepdfapp-env | Green  | N/A          | 64bit Amazon Linux 2014.09 v1.2.0 running Docker 1.3.3 | Ready  | N/A          | WebServer::Standard::  | samplepdf.Dockerfile

CMD_CREATE_ENV = "elastic-beanstalk-create-environment -j -s '64bit Amazon Linux 2014.09 v1.2.0 running Docker 1.3.3' "
#elastic-beanstalk-create-environment -j -s '64bit Amazon Linux 2014.09 v1.2.0 running Docker 1.3.3' -a samplepdfapp -e samplepdfapp-env -f env.json
#{"CreateEnvironmentResponse":{"CreateEnvironmentResult":{"AbortableOperationInProgress":null,"Alerts":null,"ApplicationName":"samplepdfapp","CNAME":null,"DateCreated":1.427205292936E9,"DateUpdated":1.427205292936E9,"Description":null,"EndpointURL":null,"EnvironmentId":"e-br3cu4t3gv","EnvironmentName":"samplepdfapp-env","Health":"Grey","HealthStatus":null,"Resources":null,"SolutionStackName":"64bit Amazon Linux 2014.09 v1.2.0 running Docker 1.3.3","Status":"Launching","TemplateName":null,"Tier":{"Name":"WebServer","Type":"Standard","Version":" "},"VersionLabel":null},"ResponseMetadata":{"RequestId":"cae72f60-f009-4d11-8e1a-5f699abf01a3"}}}

S3_SOURCE = "dreyou.docker/samplepdf/Dockerfile"

CREATE_ENV_OPTS = """
[
  {"Namespace": "aws:autoscaling:asg",
   "OptionName": "MinSize",
   "Value": "1"},
  {"Namespace": "aws:autoscaling:asg",
   "OptionName": "MaxSize",
   "Value": "1"},
  {"Namespace": "aws:autoscaling:launchconfiguration",
   "OptionName": "InstanceType",
   "Value": "t1.micro"},
  {"Namespace": "aws:elasticbeanstalk:environment",
   "OptionName": "EnvironmentType",
   "Value": "SingleInstance"}
]
"""

def runCmd(cmd):
    logging.debug("Run: "+cmd)
    res = None
    try:
        res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
        logging.debug(res)
    except:
        logging.exception("Can't run command: "+str(sys.exc_info()[0]))
    return res

def rebuildEnv(name):
    logging.info("Rebuild environment for application: "+name)
    obj = None
    try:
        if getEnvStatus(name) != ("Ready", "Green"):
            logging.error("Can't find environment in good state")
            return None
        env = getEnv(name)
        out = runCmd(CMD_REBUILD+" -e "+env["EnvironmentName"])
        obj = json.loads(out)
        if isError(obj):
            return None
    except:
        logging.exception("Can't convert output to json: "+str(sys.exc_info()[0]))
    return obj

def isError(resp):
    try:
        if "Error" in resp:
            logging.debug(resp)
            logging.error(resp["Error"]["Message"])
            return True
    except:
        logging.exception("Unknown error: "+str(sys.exc_info()[0]))
    return False

def getEbEnvs():
    logging.debug("Read Eb Environments: "+CMD_ENVS)
    obj = None
    try:
        out = runCmd(CMD_ENVS)
        obj = json.loads(out)
        if isError(obj):
            return None
    except:
        logging.exception("Can't convert output to json: "+str(sys.exc_info()[0]))
    return obj

def getEbApps():
    logging.debug("Read Eb Applications: "+CMD_APPS)
    obj = None
    try:
        out = runCmd(CMD_APPS)
        obj = json.loads(out)
        if isError(obj):
            return None
    except:
        logging.exception("Can't convert output to json: "+str(sys.exc_info()[0]))
    return obj

def getEnvStatus(name=""):
    env = getEnv(name)
    if env is not None:
        return str(env['Status']), str(env['Health'])
    return None, None

def getEnv(name=""):
    all = getEbEnvs()
    if all is None:
        return None, None
    envs = all['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments']
    if len(envs) == 0:
        return None, None
    for env in envs:
        if env['ApplicationName'] == name and env['Status'] != "Terminated":
            return env

    return None


def mock_cmd(cmd):
    if cmd.startswith(CMD_ENVS):
        return '{"DescribeEnvironmentsResponse":{"DescribeEnvironmentsResult":{"Environments":[{"AbortableOperationInProgress":false,"Alerts":[],"ApplicationName":"samplepdfapp","CNAME":"samplepdfapp-env.elasticbeanstalk.com","DateCreated":1.426967923855E9,"DateUpdated":1.427117121336E9,"Description":null,"EndpointURL":"107.20.239.203","EnvironmentId":"e-krxppb6mw6","EnvironmentName":"samplepdfapp-env","Health":"Green","HealthStatus":null,"Resources":null,"SolutionStackName":"64bit Amazon Linux 2014.09 v1.2.0 running Docker 1.3.3","Status":"Ready","TemplateName":null,"Tier":{"Name":"WebServer","Type":"Standard","Version":" "},"VersionLabel":"samplepdf.Dockerfile"}]},"ResponseMetadata":{"RequestId":"6623e942-4c84-4f1f-bc47-42cd40fdd11d"}}}'
    if cmd.startswith(CMD_APPS):
        return '{"DescribeApplicationsResponse":{"DescribeApplicationsResult":{"Applications":[{"ApplicationName":"samplepdfapp","ConfigurationTemplates":[],"DateCreated":1.426966683448E9,"DateUpdated":1.426966683448E9,"Description":null,"Versions":["samplepdf.Dockerfile"]}]},"ResponseMetadata":{"RequestId":"6ae3674c-3b45-482f-b087-d56380496bd2"}}}'
    if cmd.startswith(CMD_REBUILD):
        return '{"RebuildEnvironmentResponse":{"ResponseMetadata":{"RequestId":"dc66857e-0d90-46ed-bba8-b3d7ba720bc8"}}}'


class EbLocalTestCase(unittest.TestCase):

    def setUp(self):
        self.saveCmd = sys.modules[__name__].runCmd

    def tearDown(self):
        sys.modules[__name__].runCmd = self.saveCmd

    def test_cmdRun(self):
        res = runCmd("ls -la")
        self.assertNotEqual(res, None)
        self.assertNotEqual(res, "abc")

    def test_mockCmdRun(self):
        sys.modules[__name__].runCmd = lambda c: "abc"
        res = runCmd("ls -la")
        self.assertEqual(res, "abc")

    def test_getEbEnvs(self):
        sys.modules[__name__].runCmd = lambda c: mock_cmd(c)
        data = getEbEnvs()
        self.assertNotEqual(data, None)
        envs = data['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments']
        self.assertNotEqual(envs, None)
        self.assertTrue(len(envs) > 0)
        self.assertNotEqual(envs[0]['ApplicationName'], None)

    def test_getEnv(self):
        sys.modules[__name__].runCmd = lambda c: mock_cmd(c)
        self.assertNotEqual(getEnv("samplepdfapp"), None)
        self.assertEqual(getEnv("samplepdfapp")['ApplicationName'], "samplepdfapp")
        self.assertEqual(getEnv("samplepdfapp")["EnvironmentName"], "samplepdfapp-env")

    def test_getEnvStatus(self):
        sys.modules[__name__].runCmd = lambda c:  mock_cmd(c)
        self.assertEqual(getEnvStatus("samplepdfapp"), ("Ready", "Green"))
        self.assertEqual(getEnvStatus("unknownapp"), (None, None))

    def test_getEbApps(self):
        sys.modules[__name__].runCmd = lambda c:  mock_cmd(c)
        data = getEbApps()
        self.assertNotEqual(data, None)
        apps = data['DescribeApplicationsResponse']['DescribeApplicationsResult']['Applications']
        self.assertNotEqual(apps, None)
        self.assertTrue(len(apps) > 0)
        self.assertNotEqual(apps[0]['ApplicationName'], None)

    def test_isError(self):
        clean = '{"DescribeApplicationsResponse":{"DescribeApplicationsResult":{"Applications":[{"ApplicationName":"samplepdfapp","ConfigurationTemplates":[],"DateCreated":1.426966683448E9,"DateUpdated":1.426966683448E9,"Description":null,"Versions":["samplepdf.Dockerfile"]}]},"ResponseMetadata":{"RequestId":"6ae3674c-3b45-482f-b087-d56380496bd2"}}}'
        error = '{"Error":{"Code":"ValidationError","Message":"1 validation error detected: Value \'zzz\' at \'environmentName\' failed to satisfy constraint: Member must have length greater than or equal to 4","Type":"Sender"},"RequestId":"82766cd4-9666-4ec7-84f7-f544b7c61149"}'
        obj = json.loads(clean)
        self.assertFalse(isError(obj))
        obj = json.loads(error)
        self.assertTrue(isError(obj))

    def test_rebuildEnv(self):
        sys.modules[__name__].runCmd = lambda c:  mock_cmd(c)
        res = rebuildEnv("samplepdfapp")
        self.assertNotEqual(res, None)
        self.assertTrue("RebuildEnvironmentResponse" in res)
        self.assertNotEqual(res["RebuildEnvironmentResponse"]["ResponseMetadata"]["RequestId"], None)
        res = rebuildEnv("unknownapp")
        self.assertEqual(res, None)

if __name__ == '__main__':
    unittest.main()
