package util

import (
	"fmt"
	"io/ioutil"
	userOS "os/user"
	"reflect"
	"strings"
)

func GetHome() (string, error) {
	user, err := userOS.Current()
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("%s/.smarttune", user.HomeDir), nil
}

func GetSupportedSystem(dir string) ([]string, error) {
	var supportedSystem []string
	fileInfoList, err := ioutil.ReadDir(dir)
	if err != nil {
		return supportedSystem, err
	}
	for i := range fileInfoList {
		if fileInfoList[i].IsDir() && Contain(fileInfoList[i].Name(), "@") {
			supportedSystem = append(supportedSystem, fileInfoList[i].Name())
		}
	}
	return supportedSystem, nil
}

func Contain(list interface{}, target interface{}) bool {
	if reflect.TypeOf(list).Kind() == reflect.Slice || reflect.TypeOf(list).Kind() == reflect.Array {
		listValue := reflect.ValueOf(list)
		for i := 0; i < listValue.Len(); i++ {
			if target == listValue.Index(i).Interface() {
				return true
			}
		}
	}
	if reflect.TypeOf(target).Kind() == reflect.String && reflect.TypeOf(list).Kind() == reflect.String {
		return strings.Contains(list.(string), target.(string))
	}
	return false
}
