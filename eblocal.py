#EB Utils
import subprocess
import json
import logging
import sys
import unittest
import os
import tempfile
import time
from mock import Mock

CMD_ENVS = "elastic-beanstalk-describe-environments -j"
CMD_APPS = "elastic-beanstalk-describe-applications -j"
CMD_REBUILD = "elastic-beanstalk-rebuild-environment -j"
#elastic-beanstalk-delete-application -j -f -a samplepdfapp
CMD_DELETE = "elastic-beanstalk-delete-application -j -f"
#elastic-beanstalk-create-application-version -j -c -a samplepdfapp -s dreyou.docker/samplepdf/Dockerfile -l samplepdfapp.Docker
CMD_CREATE_APP = "elastic-beanstalk-create-application-version -j -c"
#elastic-beanstalk-create-environment -j -s '64bit Amazon Linux 2014.09 v1.2.0 running Docker 1.3.3' -a samplepdfapp -e samplepdfapp-env -c samplepdfapp-env -f env.json -l samplepdfapp.Docker
CMD_CREATE_ENV = "elastic-beanstalk-create-environment -j -s '64bit Amazon Linux 2015.09 v2.0.8 running Docker 1.9.1' "

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
  {"Namespace": "aws:autoscaling:launchconfiguration",
   "OptionName": "IamInstanceProfile",
   "Value": "aws-elasticbeanstalk-ec2-role"},
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

def createAppVersion(name, source):
    return name+".Docker"

def createEnvName(name):
    return name+"-env"

def createParFile(name):
    par_file_name = tempfile.mktemp(prefix=name)
    par_file = open(par_file_name, "w")
    par_file.write(CREATE_ENV_OPTS)
    par_file.close()
    return par_file_name

def deleteParFile(par_file_name):
    if os.path.exists(par_file_name):
        os.unlink(par_file_name)

def createApp(name, source):
    logging.info("Creating application: "+name)
    obj = None
    try:
        if getEnvStatus(name) == ("Ready", "Green"):
            logging.error("Application environment already exists and in good state")
            return None
        ver = createAppVersion(name, source)
        out = runCmd(CMD_CREATE_APP+" -a "+name+" -s "+source+" -l "+ver)
        obj = json.loads(out)
        if isError(obj):
            return None
    except:
        logging.exception("Error while creating application: "+str(sys.exc_info()[0]))
    return obj

def createEnv(name, source):
    logging.info("Creating environment for application: "+name)
    obj = None
    try:
        if getEnvStatus(name) == ("Ready", "Green"):
            logging.error("Application environment already exists and in good state")
            return None
        env = createEnvName(name)
        ver = createAppVersion(name, source)
        par_file_name = createParFile(name)
        out = runCmd(CMD_CREATE_ENV+" -a "+name+" -e "+env+" -c "+env+" -l "+ver+" -f "+par_file_name)
        deleteParFile(par_file_name)
        obj = json.loads(out)
        if isError(obj):
            return None
    except:
        logging.exception("Error while creating application environment: "+str(sys.exc_info()[0]))
    return obj


def deleteApp(name):
    logging.info("Deleting application: "+name)
    obj = None
    try:
        if getEnvStatus(name) != ("Ready", "Green"):
            logging.error("Can't find application environment in good state")
            return None
        out = runCmd(CMD_DELETE+" -a "+name)
        obj = json.loads(out)
        if isError(obj):
            return None
    except:
        logging.exception("Error while deleting application: "+str(sys.exc_info()[0]))
    return obj

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
        logging.exception("Error while rebuilding environment: "+str(sys.exc_info()[0]))
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

def getEnvAge(name=""):
    env = getEnv(name)
    if env is None:
        return None
    now = time.time()
    try:
        diff = now - env["DateUpdated"]
        hours, rest = divmod(diff, 3600)
        return hours
    except:
        logging.exception("Can't calculate environment age: "+str(sys.exc_info()[0]))
        return None

def getEnv(name=""):
    all = getEbEnvs()
    if all is None:
        return None
    envs = all['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments']
    if len(envs) == 0:
        return None
    for env in envs:
        if env['ApplicationName'] == name and env['Status'] != "Terminated":
            return env

    return None

class EbLocalTestCase(unittest.TestCase):

    mock_res_add = ""

    mock_res = dict()
    mock_res[CMD_ENVS] = '{"DescribeEnvironmentsResponse":{"DescribeEnvironmentsResult":{"Environments":[{"AbortableOperationInProgress":false,"Alerts":[],"ApplicationName":"samplepdfapp","CNAME":"samplepdfapp-env.elasticbeanstalk.com","DateCreated":1.426967923855E9,"DateUpdated":1.427117121336E9,"Description":null,"EndpointURL":"107.20.239.203","EnvironmentId":"e-krxppb6mw6","EnvironmentName":"samplepdfapp-env","Health":"Green","HealthStatus":null,"Resources":null,"SolutionStackName":"64bit Amazon Linux 2014.09 v1.2.0 running Docker 1.3.3","Status":"Ready","TemplateName":null,"Tier":{"Name":"WebServer","Type":"Standard","Version":" "},"VersionLabel":"samplepdf.Dockerfile"}]},"ResponseMetadata":{"RequestId":"6623e942-4c84-4f1f-bc47-42cd40fdd11d"}}}'
    mock_res[CMD_ENVS+"0"] = '{"DescribeEnvironmentsResponse":{"DescribeEnvironmentsResult":{"Environments":[]},"ResponseMetadata":{"RequestId":"6623e942-4c84-4f1f-bc47-42cd40fdd11d"}}}'
    mock_res[CMD_APPS] = '{"DescribeApplicationsResponse":{"DescribeApplicationsResult":{"Applications":[{"ApplicationName":"samplepdfapp","ConfigurationTemplates":[],"DateCreated":1.426966683448E9,"DateUpdated":1.426966683448E9,"Description":null,"Versions":["samplepdf.Dockerfile"]}]},"ResponseMetadata":{"RequestId":"6ae3674c-3b45-482f-b087-d56380496bd2"}}}'
    mock_res[CMD_APPS+"0"] = '{"DescribeApplicationsResponse":{"DescribeApplicationsResult":{"Applications":[]}]},"ResponseMetadata":{"RequestId":"6ae3674c-3b45-482f-b087-d56380496bd2"}}}'
    mock_res[CMD_REBUILD] = '{"RebuildEnvironmentResponse":{"ResponseMetadata":{"RequestId":"dc66857e-0d90-46ed-bba8-b3d7ba720bc8"}}}'
    mock_res[CMD_DELETE] = '{"DeleteApplicationResponse":{"ResponseMetadata":{"RequestId":"8f004d68-33f2-43b7-b930-679566f7cd15"}}}'
    mock_res[CMD_CREATE_APP] = '{"CreateApplicationVersionResponse":{"CreateApplicationVersionResult":{"ApplicationVersion":{"ApplicationName":"samplepdfapp","DateCreated":1.427205143742E9,"DateUpdated":1.427205143742E9,"Description":null,"SourceBundle":{"S3Bucket":"dreyou.docker","S3Key":"samplepdf/Dockerfile"},"VersionLabel":"samplepdfapp.Docker"}},"ResponseMetadata":{"RequestId":"d52bb9d7-5b57-4903-b32d-f349b9247fd1"}}}'
    mock_res[CMD_CREATE_ENV] = '{"CreateEnvironmentResponse":{"CreateEnvironmentResult":{"AbortableOperationInProgress":null,"Alerts":null,"ApplicationName":"samplepdfapp","CNAME":"samplepdfapp-env.elasticbeanstalk.com","DateCreated":1.427206057439E9,"DateUpdated":1.427206057439E9,"Description":null,"EndpointURL":null,"EnvironmentId":"e-ycgxfs5cay","EnvironmentName":"samplepdfapp-env","Health":"Grey","HealthStatus":null,"Resources":null,"SolutionStackName":"64bit Amazon Linux 2014.09 v1.2.0 running Docker 1.3.3","Status":"Launching","TemplateName":null,"Tier":{"Name":"WebServer","Type":"Standard","Version":" "},"VersionLabel":null},"ResponseMetadata":{"RequestId":"c933084a-82d3-46a8-b97c-ad0d246267e1"}}}'

    def mock_cmd(self, cmd):
        if cmd.startswith(CMD_ENVS):
            return self.mock_res[CMD_ENVS+self.mock_res_add]
        if cmd.startswith(CMD_APPS):
            return self.mock_res[CMD_APPS+self.mock_res_add]
        if cmd.startswith(CMD_REBUILD):
            return self.mock_res[CMD_REBUILD]
        if cmd.startswith(CMD_DELETE):
            return self.mock_res[CMD_DELETE]
        if cmd.startswith(CMD_CREATE_APP):
            return self.mock_res[CMD_CREATE_APP]
        if cmd.startswith(CMD_CREATE_ENV):
            return self.mock_res[CMD_CREATE_ENV]

    def setUp(self):
        self.saveCmd = sys.modules[__name__].runCmd
        self.mock_res_add = ""

    def tearDown(self):
        sys.modules[__name__].runCmd = self.saveCmd
        self.mock_res_add = ""

    def test_cmdRun(self):
        res = runCmd("ls -la")
        self.assertNotEqual(res, None)
        self.assertNotEqual(res, "abc")

    def test_mockCmdRun(self):
        sys.modules[__name__].runCmd = lambda c: "abc"
        res = runCmd("ls -la")
        self.assertEqual(res, "abc")

    def test_getEbEnvs(self):
        sys.modules[__name__].runCmd = self.mock_cmd
        data = getEbEnvs()
        self.assertNotEqual(data, None)
        envs = data['DescribeEnvironmentsResponse']['DescribeEnvironmentsResult']['Environments']
        self.assertNotEqual(envs, None)
        self.assertTrue(len(envs) > 0)
        self.assertNotEqual(envs[0]['ApplicationName'], None)

    def test_getEnv(self):
        sys.modules[__name__].runCmd = self.mock_cmd
        self.assertNotEqual(getEnv("samplepdfapp"), None)
        self.assertEqual(getEnv("samplepdfapp")['ApplicationName'], "samplepdfapp")
        self.assertEqual(getEnv("samplepdfapp")["EnvironmentName"], "samplepdfapp-env")

    def test_getEnvStatus(self):
        sys.modules[__name__].runCmd = self.mock_cmd
        self.assertEqual(getEnvStatus("samplepdfapp"), ("Ready", "Green"))
        self.assertEqual(getEnvStatus("unknownapp"), (None, None))

    def test_getEbApps(self):
        sys.modules[__name__].runCmd = self.mock_cmd
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
        sys.modules[__name__].runCmd = self.mock_cmd
        res = rebuildEnv("samplepdfapp")
        self.assertNotEqual(res, None)
        self.assertTrue("RebuildEnvironmentResponse" in res)
        self.assertNotEqual(res["RebuildEnvironmentResponse"]["ResponseMetadata"]["RequestId"], None)
        res = rebuildEnv("unknownapp")
        self.assertEqual(res, None)

    def test_deleteApp(self):
        sys.modules[__name__].runCmd = self.mock_cmd
        res = deleteApp("samplepdfapp")
        self.assertNotEqual(res, None)
        self.assertTrue("DeleteApplicationResponse" in res)
        self.assertNotEqual(res["DeleteApplicationResponse"]["ResponseMetadata"]["RequestId"], None)
        res = deleteApp("unknownapp")
        self.assertEqual(res, None)

    def test_createApp(self):
        sys.modules[__name__].runCmd = self.mock_cmd
        self.mock_res_add = "0"
        res = createApp("samplepdfapp", "dreyou.docker/samplepdf/Dockerfile")
        self.assertNotEqual(res, None)
        self.assertTrue("CreateApplicationVersionResponse" in res)
        res = createEnv("samplepdfapp", "dreyou.docker/samplepdf/Dockerfile")
        self.assertNotEqual(res, None)
        self.assertTrue("CreateEnvironmentResponse" in res)

    def test_notCreateApp(self):
        sys.modules[__name__].runCmd = self.mock_cmd
        res = createApp("samplepdfapp", "dreyou.docker/samplepdf/Dockerfile")
        self.assertEqual(res, None)

    def test_timeOfEnv(self):
        sys.modules[__name__].runCmd = self.mock_cmd
        res = getEnv("samplepdfapp")
        self.assertNotEqual(res, None)
        etime = time.ctime(res["DateUpdated"])
        self.assertNotEqual(etime, None)
        hours = getEnvAge("samplepdfapp")
        self.assertNotEqual(hours, None)
        self.assertTrue(hours > 24)
        hours = getEnvAge("unknownapp")
        self.assertEqual(hours, None)

if __name__ == '__main__':
    unittest.main()
