#!/usr/bin/env python
# encoding: utf-8
import logging
import json
import os
import urlparse

from suds.client import Client
import xmltodict


MAX_CHECK_COUNT = 5
logger = logging.getLogger(__name__)
_current_path = os.path.dirname(os.path.realpath(__file__))
_wsdl = os.path.join(_current_path, 'NciicServices.wsdl')
_url = urlparse.urljoin('file://', _wsdl)
_inlicense = r'shouquanwenjianneirong'  # 授权文件字符串
_client = Client(_url)


def _init_inconditions(dict_data):
    rows = {
        "ROWS": {
            "INFO": {"SBM": u"机构名称"},
            "ROW": [
                {"GMSFHM": u"公民身份号码",
                 "XM": u"姓名"},
                {"GMSFHM": dict_data['id_number'],
                 "XM": dict_data['name'],
                 "@FSD": u'上海',
                 "@YWLX": 'eleme'}
            ]
        }
    }
    return xmltodict.unparse(rows)


def _parse_result(resp_xml):
    result = xmltodict.parse(resp_xml, encoding='utf-8')
    if 'RESPONSE' in result:
        error_xml = json.dumps(result['RESPONSE'])
        logger.error('NciicServiceError:' + error_xml, ensure_ascii=False)
        raise('NCIIC_SERVICE_ERROR', error_xml)
    else:
        row = result['ROWS']['ROW']
        items = row['OUTPUT']['ITEM']
        if 'gmsfhm' in items[0]:
            if items[0]['result_gmsfhm'] == items[1]['result_xm']:
                return True
            else:
                logger.info('CERTIFY_FAILED:' +
                            json.dumps(row, ensure_ascii=False))
                return False
        elif 'errormesage' in items[0]:
            # 我真不想吐槽这个mesage单词了
            logger.info('CERTIFY_FAILED:' +
                        json.dumps(row, ensure_ascii=False))
            return False


def nciic_check(dict_data):
    '''dict_data = {'id_number': <id_number>, 'name': <name>}
    return: True/False
    '''

    incondition = _init_inconditions(dict_data)
    resp_xml = _client.service.nciicCheck(_inlicense, incondition)
    return _parse_result(resp_xml)
