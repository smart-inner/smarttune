package http

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	netUrl "net/url"
	"strings"
)

// UploadFile
// @Description: defines a file to be uploaded
type UploadFile struct {
	Name     string
	Filepath string
}

var httpClient = &http.Client{}

// HandleResponse
// @Description: handle HTTP response
// @Parameter *http.Response
// @return string
// @return error
func HandleResponse(response *http.Response) (string, error) {
	body, err := ioutil.ReadAll(response.Body)
	if err != nil {
		return "", err
	}
	var build strings.Builder
	build.WriteString(string(body))
	build.WriteString("\n")
	if response.StatusCode != 200 {
		return "", errors.New(build.String())
	}
	return build.String(), nil
}

// Get
// @Description: implement HTTP GET
// @Parameter url
// @Parameter request
// @return *http.Response
// @return error
func Get(url string, request map[string]string) (*http.Response, error) {
	urlParams := netUrl.Values{}
	parsedURL, _ := netUrl.Parse(url)
	for key, val := range request {
		urlParams.Set(key, val)
	}

	parsedURL.RawQuery = urlParams.Encode()
	urlPath := parsedURL.String()

	httpRequest, _ := http.NewRequest("GET", urlPath, nil)
	resp, err := httpClient.Do(httpRequest)
	if err != nil {
		return nil, err
	}
	return resp, nil
}

// PostJSON
// @Description: implements HTTP POST with JSON format
// @Parameter url
// @Parameter request
// @return *http.Response
// @return error
func PostJSON(url string, request map[string]interface{}) (*http.Response, error) {
	return post(url, request, "application/json")
}

// post
// @Description: common handle post request
// @Parameter url
// @Parameter request
// @Parameter contentType
// @Parameter files
// @return *http.Response
// @return error
func post(url string, request map[string]interface{}, contentType string) (*http.Response, error) {
	return postOrPut("POST", url, request, contentType)
}

func postOrPut(method string, url string, request map[string]interface{}, contentType string) (*http.Response, error) {
	if request == nil {
		return nil, errors.New("the request parameter cannot be nil")
	}
	requestBody, realContentType, err := getReader(request, contentType)
	if err != nil {
		return nil, err
	}
	httpRequest, _ := http.NewRequest(method, url, requestBody)
	httpRequest.Header.Add("Content-Type", realContentType)
	resp, err := httpClient.Do(httpRequest)
	if err != nil {
		return nil, err
	}
	return resp, nil
}

// getReader
// @Description: get reader data
// @Parameter request
// @Parameter contentType
// @Parameter files
// @return io.Reader
// @return string
// @return error
func getReader(request map[string]interface{}, contentType string) (io.Reader, string, error) {
	if strings.Contains(contentType, "json") {
		bytesData, _ := json.Marshal(request)
		return bytes.NewReader(bytesData), contentType, nil
	} else {
		urlValues := netUrl.Values{}
		for key, val := range request {
			urlValues.Set(key, fmt.Sprint(val))
		}
		reqBody := urlValues.Encode()
		return strings.NewReader(reqBody), contentType, nil
	}
}

func Delete(url string) (*http.Response, error) {
	httpRequest, _ := http.NewRequest("DELETE", url, nil)
	resp, err := httpClient.Do(httpRequest)
	if err != nil {
		return nil, err
	}
	return resp, nil
}
